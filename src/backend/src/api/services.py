from __future__ import annotations

import datetime as dt
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.backend.src.db.models import UnderlyingView


SORT_FIELDS = {
    "date": UnderlyingView.date,
    "confidence": UnderlyingView.confidence,
    "underlying": UnderlyingView.underlying,
    "bank": UnderlyingView.bank,
    "sentiment": UnderlyingView.sentiment,
}

SENTIMENT_ORDER = ["bullish", "bearish", "neutral"]
CONFIDENCE_BUCKETS = [
    ("0-20", 0, 20),
    ("21-40", 21, 40),
    ("41-60", 41, 60),
    ("61-80", 61, 80),
    ("81-100", 81, 100),
]


def parse_date_param (value : Optional[str], field_name : str) -> Optional[dt.date] :
    """
    Parse a YYYY-MM-DD query parameter.
    """
    if not value :
        return None
    
    try :
        return dt.date.fromisoformat(value)
    
    except ValueError as exc :
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}. Expected YYYY-MM-DD.") from exc


def serialize_view (view : UnderlyingView) -> Dict[str, Any] :
    """
    Serialize an ORM view row into an API payload.
    """
    return {
        "id": view.id,
        "email_id": view.email_id,
        "underlying": view.underlying,
        "sentiment": view.sentiment,
        "bank": view.bank,
        "date": str(view.date) if view.date else "",
        "rationale": view.rationale or "",
        "levels": view.levels or "",
        "confidence": int(view.confidence or 0),
    }


def apply_view_filters(
    query,
    *,
    underlying : Optional[str] = None,
    bank : Optional[str] = None,
    sentiment : Optional[str] = None,
    start_date : Optional[str] = None,
    end_date : Optional[str] = None,
    search : Optional[str] = None,
) :
    """
    Apply all supported filters to a view query.
    """
    start_date_value = parse_date_param(start_date, "start_date")
    end_date_value = parse_date_param(end_date, "end_date")

    if underlying :
        query = query.filter(UnderlyingView.underlying == underlying.upper())
    
    if bank :
        query = query.filter(UnderlyingView.bank.ilike(f"%{bank}%"))
    
    if sentiment :
        query = query.filter(UnderlyingView.sentiment == sentiment.lower())
    
    if start_date_value :
        query = query.filter(UnderlyingView.date >= start_date_value)
    
    if end_date_value :
        query = query.filter(UnderlyingView.date <= end_date_value)
    
    if search :
        like_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                UnderlyingView.underlying.ilike(like_term),
                UnderlyingView.bank.ilike(like_term),
                UnderlyingView.rationale.ilike(like_term),
                UnderlyingView.levels.ilike(like_term),
            )
        )
    
    return query


def sort_query (query, sort_by : str, sort_order : str) :
    """
    Apply ordering to a query.
    """
    if sort_by not in SORT_FIELDS :
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by. Expected one of: {', '.join(sorted(SORT_FIELDS))}.",
        )
    
    if sort_order not in {"asc", "desc"} :
        raise HTTPException(status_code=400, detail="Invalid sort_order. Expected 'asc' or 'desc'.")

    sort_column = SORT_FIELDS[sort_by]
    ordered = sort_column.asc() if sort_order == "asc" else sort_column.desc()
    return query.order_by(ordered, UnderlyingView.id.desc())


def build_views_query(
    db : Session,
    *,
    underlying : Optional[str] = None,
    bank : Optional[str] = None,
    sentiment : Optional[str] = None,
    start_date : Optional[str] = None,
    end_date : Optional[str] = None,
    search : Optional[str] = None,
) :
    """
    Build the filtered query for underlying views.
    """
    query = db.query(UnderlyingView)
    return apply_view_filters(
        query,
        underlying=underlying,
        bank=bank,
        sentiment=sentiment,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )


def percentage (count : int, total : int) -> float :
    """
    Convert a count into a percentage of the total.
    """
    if total <= 0 :
        return 0.0
    
    return round((count / total) * 100, 1)


def bucket_for_confidence (confidence : int) -> str :
    """
    Map a confidence integer to a display bucket.
    """
    for label, low, high in CONFIDENCE_BUCKETS :
        if low <= confidence <= high :
            return label
    
    return CONFIDENCE_BUCKETS[-1][0]


def empty_dashboard_payload (filters_applied : Dict[str, Any]) -> Dict[str, Any] :
    """
    Build the default dashboard payload when there are no rows.
    """
    return {
        "filters_applied": filters_applied,
        "summary": {
            "total_views": 0,
            "avg_confidence": 0.0,
            "bullish_count": 0,
            "bearish_count": 0,
            "neutral_count": 0,
            "unique_underlyings": 0,
            "unique_banks": 0,
            "latest_date": None,
        },
        "sentiment_breakdown": [
            {"label": label.title(), "key": label, "count": 0, "share": 0.0}
            for label in SENTIMENT_ORDER
        ],
        "confidence_breakdown": [
            {"label": label, "count": 0, "share": 0.0}
            for label, _, _ in CONFIDENCE_BUCKETS
        ],
        "top_underlyings": [],
        "top_banks": [],
        "timeline": [],
        "recent_views": [],
    }


def build_dashboard_payload(
    views : List[UnderlyingView],
    *,
    filters_applied : Dict[str, Any],
    recent_limit : int,
    top_n : int,
) -> Dict[str, Any] :
    """
    Aggregate rows into the dashboard response payload.
    """
    if not views :
        return empty_dashboard_payload(filters_applied)

    total_views = len(views)
    sentiment_counter = Counter()
    confidence_counter = Counter({label: 0 for label, _, _ in CONFIDENCE_BUCKETS})
    timeline_map: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "date": "",
            "total": 0,
            "bullish": 0,
            "bearish": 0,
            "neutral": 0,
            "confidence_sum": 0,
        }
    )
    underlying_map: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "confidence_sum": 0, "bullish": 0, "bearish": 0, "neutral": 0}
    )
    bank_map: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "confidence_sum": 0, "bullish": 0, "bearish": 0, "neutral": 0}
    )

    confidence_sum = 0
    unique_underlyings = set()
    unique_banks = set()

    sorted_recent = sorted(
        views,
        key=lambda item: (item.date or dt.date.min, item.confidence or 0, item.id or 0),
        reverse=True,
    )

    for view in views :
        confidence = int(view.confidence or 0)
        sentiment = (view.sentiment or "neutral").lower()
        view_date = str(view.date) if view.date else ""

        sentiment_counter[sentiment] += 1
        confidence_counter[bucket_for_confidence(confidence)] += 1
        confidence_sum += confidence
        unique_underlyings.add(view.underlying)
        unique_banks.add(view.bank)

        timeline_bucket = timeline_map[view_date]
        timeline_bucket["date"] = view_date
        timeline_bucket["total"] += 1
        timeline_bucket["confidence_sum"] += confidence
        
        if sentiment in {"bullish", "bearish", "neutral"} :
            timeline_bucket[sentiment] += 1

        underlying_bucket = underlying_map[view.underlying]
        underlying_bucket["count"] += 1
        underlying_bucket["confidence_sum"] += confidence
        
        if sentiment in {"bullish", "bearish", "neutral"} :
            underlying_bucket[sentiment] += 1

        bank_bucket = bank_map[view.bank]
        bank_bucket["count"] += 1
        bank_bucket["confidence_sum"] += confidence
        
        if sentiment in {"bullish", "bearish", "neutral"} :
            bank_bucket[sentiment] += 1

    def build_rankings (source_map : Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]] :
        """
        Build the ranking sections for underlyings and banks.
        """
        items = []
        
        for label, payload in source_map.items() :
            count = payload["count"]
            items.append(
                {
                    "label": label,
                    "count": count,
                    "share": percentage(count, total_views),
                    "avg_confidence": round(payload["confidence_sum"] / count, 1) if count else 0.0,
                    "bullish": payload["bullish"],
                    "bearish": payload["bearish"],
                    "neutral": payload["neutral"],
                }
            )
        
        items.sort(key=lambda item: (-item["count"], -item["avg_confidence"], item["label"]))
        return items[:top_n]

    timeline = []
    
    for date_key in sorted(timeline_map.keys()) :
        bucket = timeline_map[date_key]
        total = bucket["total"]
        timeline.append(
            {
                "date": date_key,
                "total": total,
                "bullish": bucket["bullish"],
                "bearish": bucket["bearish"],
                "neutral": bucket["neutral"],
                "avg_confidence": round(bucket["confidence_sum"] / total, 1) if total else 0.0,
            }
        )

    return {
        "filters_applied": filters_applied,
        "summary": {
            "total_views": total_views,
            "avg_confidence": round(confidence_sum / total_views, 1) if total_views else 0.0,
            "bullish_count": sentiment_counter["bullish"],
            "bearish_count": sentiment_counter["bearish"],
            "neutral_count": sentiment_counter["neutral"],
            "unique_underlyings": len(unique_underlyings),
            "unique_banks": len(unique_banks),
            "latest_date": timeline[-1]["date"] if timeline else None,
        },
        "sentiment_breakdown": [
            {
                "label": label.title(),
                "key": label,
                "count": sentiment_counter[label],
                "share": percentage(sentiment_counter[label], total_views),
            }
            for label in SENTIMENT_ORDER
        ],
        "confidence_breakdown": [
            {
                "label": label,
                "count": confidence_counter[label],
                "share": percentage(confidence_counter[label], total_views),
            }
            for label, _, _ in CONFIDENCE_BUCKETS
        ],
        "top_underlyings": build_rankings(underlying_map),
        "top_banks": build_rankings(bank_map),
        "timeline": timeline,
        "recent_views": [serialize_view(view) for view in sorted_recent[:recent_limit]],
    }


def build_filter_options (views : List[UnderlyingView]) -> Dict[str, Any] :
    """
    Build filter metadata from a set of rows.
    """
    underlying_counter = Counter(view.underlying for view in views if view.underlying)
    bank_counter = Counter(view.bank for view in views if view.bank)
    dates = [view.date for view in views if view.date]

    underlyings = [
        {"value": value, "count": count}
        for value, count in sorted(underlying_counter.items(), key=lambda item: (-item[1], item[0]))
    ]
    banks = [
        {"value": value, "count": count}
        for value, count in sorted(bank_counter.items(), key=lambda item: (-item[1], item[0]))
    ]

    return {
        "underlyings": underlyings,
        "banks": banks,
        "sentiments": [
            {"value": sentiment, "count": sum(1 for view in views if (view.sentiment or "").lower() == sentiment)}
            for sentiment in SENTIMENT_ORDER
        ],
        "date_bounds": {
            "min": str(min(dates)) if dates else None,
            "max": str(max(dates)) if dates else None,
        },
        "result_count": len(views),
    }
