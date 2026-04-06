import os
import json
import urllib.request
import urllib.error
from openai import OpenAI
from src.config.parameters import OLLAMA_URL, DEFAULT_LLM_PROVIDER, DEFAULT_LLM_MODEL

def _call_ollama(prompt: str, model: str) -> list[dict]:
    """
    Sends the prompt to a local Ollama instance and returns a parsed JSON list of views.
    """
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json" # Forces Ollama to output valid JSON
    }
    
    req = urllib.request.Request(OLLAMA_URL, headers={'Content-Type': 'application/json'}, data=json.dumps(data).encode('utf-8'))
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            response_text = result.get('response', '[]')
            
            # Simple heuristic to strip markdown backticks if the model ignored the format enforcement
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            try:
                parsed = json.loads(response_text.strip())
                if isinstance(parsed, list):
                    return parsed
                elif isinstance(parsed, dict):
                    # Sometimes models wrap it
                    for key, val in parsed.items():
                        if isinstance(val, list):
                            return val
                return []
            except json.JSONDecodeError as e:
                print(f"Ollama JSON decode error: {e}")
                print(f"Raw response: {response_text}")
                return None
    except urllib.error.URLError as e:
        print(f"Failed to connect to Ollama (Is it running?): {e}")
        return None

def _call_openai(prompt: str, model: str) -> list[dict]:
    """
    Sends the prompt to OpenAI API using the openai package.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not found in environment variables. Falling back to None.")
        return None
    
    client = OpenAI(api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model=model,
            response_format={ "type": "json_object" }, # Ensures JSON output for supported models
            messages=[
                {
                    "role": "system",
                    "content": "You are a specialized data extractor. You must ALWAYS output a JSON object containing a 'views' array."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.0
        )
        
        response_text = response.choices[0].message.content or "{}"
        
        try:
            parsed = json.loads(response_text)
            
            # OpenAI structured response format often wraps in a dictionary to strictly output a valid JSON object
            if isinstance(parsed, dict):
                # We asked for a list of views. Let's look for known keys or any list.
                if "views" in parsed and isinstance(parsed["views"], list):
                    return parsed["views"]
                for val in parsed.values():
                    if isinstance(val, list):
                        return val
                # Fallback, maybe it returned a dict wrapper for 1 view
                if "underlying" in parsed and "sentiment" in parsed:
                     return [parsed]
            
            if isinstance(parsed, list):
                 return parsed
            
            return []
        except json.JSONDecodeError as e:
            print(f"OpenAI JSON decode error: {e}")
            return None
            
    except Exception as e:
        print(f"Failed to call OpenAI API: {e}")
        return None

def extract_views_from_text(
        text: str, 
        provider: str = DEFAULT_LLM_PROVIDER, 
        model: str = DEFAULT_LLM_MODEL
    ) -> list[dict]:
    """
    Generic routing function to extract views using the desired LLM provider.
    """
    
    # We tweak the prompt slighly depending on provider if needed, 
    # but the core instructions remain identical.
    prompt = f"""
You are a financial analyst data extractor. 
I will give you an email or market commentary text. 
Your task is to extract any directional views on financial underlyings (like FX pairs, equity indices, stocks).
For each view you find, extract:
1. "underlying": The ticker or name of the asset (e.g. "EURUSD", "SPX").
2. "sentiment": One of "bullish", "bearish", or "neutral".
3. "rationale": A very short summary of why.
4. "levels": Any mentioned support, resistance, or price targets. If none, output empty string.

IMPORTANT: You must write your output STRICTLY as a JSON object containing a "views" key which holds an array of these objects, and NOTHING ELSE. If there are no views, return {{"views": []}}.

Text to process:
{text}
"""
    
    print(f"    [LLM] Requesting model: {model} via {provider}")
    
    if provider.lower() == "openai":
         return _call_openai(prompt, model)
    elif provider.lower() == "ollama":
         return _call_ollama(prompt, model)
    else:
         print(f"Unknown LLM provider: {provider}")
         return []
