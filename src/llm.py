import json
import os
import re
from typing import Any, Dict, List, Optional

import requests
from openai import OpenAI

from src.config.parameters import OLLAMA_URL


def _empty_batch_result(emails_data: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    return [[] for _ in emails_data]


def _coerce_email_id(value: Any) -> Optional[int]:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _extract_json_payload(content: str) -> Optional[Any]:
    if not content:
        return None

    candidates = [content.strip()]

    code_match = re.search(r"```(?:json)?\s*(\{.*\}|\[.*\])\s*```", content, re.DOTALL | re.IGNORECASE)
    if code_match:
        candidates.append(code_match.group(1).strip())

    json_match = re.search(r"(\{.*\}|\[.*\])", content, re.DOTALL)
    if json_match:
        candidates.append(json_match.group(1).strip())

    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def _align_views_by_email_id(
    items: List[Dict[str, Any]],
    emails_data: List[Dict[str, Any]],
) -> Optional[List[List[Dict[str, Any]]]]:
    aligned = {email["id"]: [] for email in emails_data if "id" in email}
    found_email_id = False

    for item in items:
        if not isinstance(item, dict):
            continue

        email_id = _coerce_email_id(item.get("email_id"))
        views = item.get("views")
        if email_id is None or not isinstance(views, list):
            continue

        found_email_id = True
        if email_id in aligned:
            aligned[email_id] = views

    if not found_email_id:
        return None

    return [aligned.get(email["id"], []) for email in emails_data]


def normalize_batch_result(raw_result: Any, emails_data: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """
    Normalize the many real-world JSON shapes the LLM may return.

    Preferred shape:
      {"views": [{"email_id": 123, "views": [...]}, ...]}

    Important behavior:
    - preserve email_id mapping instead of relying only on list position
    - fill missing emails with [] so processor zip() stays aligned
    """
    if raw_result is None:
        return _empty_batch_result(emails_data)

    result_body = raw_result.get("views") if isinstance(raw_result, dict) and "views" in raw_result else raw_result

    if result_body == [] or result_body == {}:
        return _empty_batch_result(emails_data)

    if isinstance(result_body, list):
        aligned = _align_views_by_email_id(result_body, emails_data)
        if aligned is not None:
            return aligned

        if all(isinstance(item, list) for item in result_body):
            return result_body

        if all(isinstance(item, dict) for item in result_body):
            return [result_body]

    if isinstance(result_body, dict):
        mapped_items = []
        for key, value in result_body.items():
            email_id = _coerce_email_id(key)
            if email_id is not None and isinstance(value, list):
                mapped_items.append({"email_id": email_id, "views": value})

        aligned = _align_views_by_email_id(mapped_items, emails_data)
        if aligned is not None:
            return aligned

    return _empty_batch_result(emails_data)


def _batch_prompt(combined_text: str) -> str:
    return f"""
    Analyze the following batch of email texts for market views on FX and Equities positioning.

    Goal:
    Extract every distinct market view mentioned in each email.

    Extraction rules:
    - Return one JSON object per distinct underlying view.
    - If one email mentions several underlyings, return several view objects for that email.
    - Do not merge several underlyings into one generic record.
    - Prefer specific underlyings such as "EURUSD", "USDJPY", "SPX", "NDX", "SXXP", "MSCI WORLD".
    - Only use a generic label like "EQUITIES" or "FX" if no specific underlying can reasonably be inferred.
    - Do not return duplicate views for the same email.
    - If an email has no actionable view, return an empty list for that email.

    Each view should have:
    - underlying: e.g. "EURUSD", "SPX"
    - sentiment: "bullish", "bearish", or "neutral"
    - bank: the bank/commentator name (infer from sender or context)
    - rationale: brief explanation focused on that underlying
    - levels: any mentioned price levels for that underlying, else ""
    - confidence: integer 0-100

    Return a JSON object with a single key "views" whose value is an array of objects.
    Each object must include:
    - email_id: the input email id
    - views: an array of view objects for that email

    Example:
    {{"views": [
        {{"email_id": 1, "views": [
            {{"underlying":"SPX","sentiment":"bullish","bank":"Goldman Sachs","rationale":"Upside positioning remains supported by flows.","levels":"6100 target","confidence":78}},
            {{"underlying":"EURUSD","sentiment":"bearish","bank":"Goldman Sachs","rationale":"Dollar strength is expected after macro data.","levels":"1.07 support","confidence":72}}
        ]}},
        {{"email_id": 2, "views": []}}
    ]}}

    Respond ONLY with valid JSON. Do not add any text outside the JSON.
    Include every new email in the snapshot and output views for the entire batch.

    Emails:
    {combined_text}
    """


def _single_email_prompt (text : str) -> str :
    return f"""
    Analyze the following email text for market views on FX and Equities positioning.

    Goal:
    Extract every distinct market view mentioned in the email.

    Extraction rules:
    - Return one JSON object per distinct underlying view.
    - If the email mentions several underlyings, return several view objects.
    - Do not merge several underlyings into one generic record.
    - Prefer specific underlyings such as "EURUSD", "USDJPY", "SPX", "NDX", "SXXP", "MSCI WORLD".
    - Only use a generic label like "EQUITIES" or "FX" if no specific underlying can reasonably be inferred.
    - Do not return duplicates.
    - If there is no actionable view, return [].

    Each view should have:
    - underlying: e.g. "EURUSD", "SPX"
    - sentiment: "bullish", "bearish", or "neutral"
    - bank: the bank/commentator name (infer from sender or context)
    - rationale: brief explanation focused on that underlying
    - levels: any mentioned price levels for that underlying, else ""
    - confidence: integer 0-100

    Example output:
    [
      {{"underlying":"SPX","sentiment":"bullish","bank":"Morgan Stanley","rationale":"Positioning and macro setup support upside.","levels":"6100 target","confidence":76}},
      {{"underlying":"EURUSD","sentiment":"bearish","bank":"Morgan Stanley","rationale":"The dollar is expected to stay supported.","levels":"1.07 support","confidence":70}}
    ]

    Respond ONLY with valid JSON.

    Email:
    {text}
    """


def extract_views_from_batch (
        
        emails_data : List[Dict[str, str]],
        provider : str = "openai",
        model : str = "gpt-4o-mini"
    
    ) -> List[List[Dict[str, Any]]] :
    """
    Extract market views from a batch of email texts using LLM.
    emails_data: list of dicts with 'id', 'body', 'sender', etc.
    Returns list of lists: for each email, a list of view dicts.
    """
    combined_text = "\n\n".join([
        f"Email {i+1} (ID: {email['id']}, Sender: {email['sender']}):\n{email['body']}"
        for i, email in enumerate(emails_data)
    ])

    prompt = _batch_prompt(combined_text)

    if provider == "openai":
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        content = response.choices[0].message.content
    elif provider == "ollama":
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        resp = requests.post(OLLAMA_URL, json=payload)
        content = resp.json().get("response", "")
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    result = _extract_json_payload(content)
    if result is None:
        print(f"Failed to parse LLM response as JSON: {content}")
        return _empty_batch_result(emails_data)

    return normalize_batch_result(result, emails_data)

def extract_views_from_text(text: str, provider: str = "openai", model: str = "gpt-4o-mini") -> List[Dict[str, Any]]:
    """
    Extract market views from a single text using LLM.
    """
    prompt = _single_email_prompt(text)

    if provider == "openai":
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        content = response.choices[0].message.content
    elif provider == "ollama":
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        resp = requests.post(OLLAMA_URL, json=payload)
        content = resp.json().get("response", "")
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    result = _extract_json_payload(content)
    if isinstance(result, list):
        return result

    if isinstance(result, dict) and isinstance(result.get("views"), list):
        return result["views"]

    print(f"Failed to parse LLM response as JSON: {content}")
    return []
