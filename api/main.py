from __future__ import annotations

import os
import sys
import argparse
import threading
import datetime as dt

from collections import Counter, defaultdict
from typing import Any, Callable, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

load_dotenv(os.path.join(ROOT_DIR, ".env"))

from src.db.database import get_db
from src.db.models import UnderlyingView
from src.processor import backfill_missing_views, process_email_range

process_state_lock = threading.Lock()
process_state = {
    "processing": False,
    "current_action": None,
    "last_run": None,
    "last_result": None,
}

SORT_FIELDS = {

    "date" : UnderlyingView.date,
    "confidence" : UnderlyingView.confidence,
    "underlying" : UnderlyingView.underlying,
    "bank" : UnderlyingView.bank,
    "sentiment" : UnderlyingView.sentiment,

}

SENTIMENT_ORDER = ["bullish", "bearish", "neutral"]

CONFIDENCE_BUCKETS = [

    ("0-20", 0, 20),
    ("21-40", 21, 40),
    ("41-60", 41, 60),
    ("61-80", 61, 80),
    ("81-100", 81, 100),

]


def _env_bool (name : str, default : bool) -> bool :
    """
    
    """
    value = os.getenv(name)
    
    if value is None :
        return default
    
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int :
    """
    
    """
    value = os.getenv(name)
    
    if value is None :
        return default
    
    try :
        return int(value)
    
    except ValueError :
        return default


def _env_csv(name: str) -> List[str] :
    """
    
    """
    value = os.getenv(name, "")
    
    return [item.strip() for item in value.split(",") if item.strip()]


allow_all_origins = _env_bool("ALLOW_ALL_ORIGINS", True)
cors_allowed_origins = _env_csv("CORS_ALLOWED_ORIGINS")
if allow_all_origins:
    resolved_allowed_origins = ["*"]
else:
    resolved_allowed_origins = cors_allowed_origins or ["http://localhost:5173"]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=resolved_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ViewResponse(BaseModel):
    id: int
    email_id: Optional[int]
    underlying: str
    sentiment: str
    bank: str
    date: str
    rationale: str
    levels: str
    confidence: int


class ProcessRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    refresh: bool = False
    provider: Optional[str] = None
    model: Optional[str] = None
    strict: bool = False


class BackfillRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None


def _parse_date_param(value: Optional[str], field_name: str) -> Optional[dt.date]:
    if not value:
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}. Expected YYYY-MM-DD.") from exc


def _serialize_view(view: UnderlyingView) -> Dict[str, Any]:
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


def _apply_view_filters(
    query,
    *,
    underlying: Optional[str] = None,
    bank: Optional[str] = None,
    sentiment: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
):
    start_date_value = _parse_date_param(start_date, "start_date")
    end_date_value = _parse_date_param(end_date, "end_date")

    if underlying:
        query = query.filter(UnderlyingView.underlying == underlying.upper())
    if bank:
        query = query.filter(UnderlyingView.bank.ilike(f"%{bank}%"))
    if sentiment:
        query = query.filter(UnderlyingView.sentiment == sentiment.lower())
    if start_date_value:
        query = query.filter(UnderlyingView.date >= start_date_value)
    if end_date_value:
        query = query.filter(UnderlyingView.date <= end_date_value)
    if search:
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


def _sort_query(query, sort_by: str, sort_order: str):
    if sort_by not in SORT_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by. Expected one of: {', '.join(sorted(SORT_FIELDS))}.",
        )
    if sort_order not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="Invalid sort_order. Expected 'asc' or 'desc'.")

    sort_column = SORT_FIELDS[sort_by]
    ordered = sort_column.asc() if sort_order == "asc" else sort_column.desc()
    return query.order_by(ordered, UnderlyingView.id.desc())


def _build_views_query(
    db: Session,
    *,
    underlying: Optional[str] = None,
    bank: Optional[str] = None,
    sentiment: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
):
    query = db.query(UnderlyingView)
    return _apply_view_filters(
        query,
        underlying=underlying,
        bank=bank,
        sentiment=sentiment,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )


def _percentage(count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((count / total) * 100, 1)


def _bucket_for_confidence(confidence: int) -> str:
    for label, low, high in CONFIDENCE_BUCKETS:
        if low <= confidence <= high:
            return label
    return CONFIDENCE_BUCKETS[-1][0]


def _empty_dashboard_payload(filters_applied: Dict[str, Any]) -> Dict[str, Any]:
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


def _build_dashboard_payload(
    views: List[UnderlyingView],
    *,
    filters_applied: Dict[str, Any],
    recent_limit: int,
    top_n: int,
) -> Dict[str, Any]:
    if not views:
        return _empty_dashboard_payload(filters_applied)

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

    for view in views:
        confidence = int(view.confidence or 0)
        sentiment = (view.sentiment or "neutral").lower()
        view_date = str(view.date) if view.date else ""

        sentiment_counter[sentiment] += 1
        confidence_counter[_bucket_for_confidence(confidence)] += 1
        confidence_sum += confidence
        unique_underlyings.add(view.underlying)
        unique_banks.add(view.bank)

        timeline_bucket = timeline_map[view_date]
        timeline_bucket["date"] = view_date
        timeline_bucket["total"] += 1
        timeline_bucket["confidence_sum"] += confidence
        if sentiment in {"bullish", "bearish", "neutral"}:
            timeline_bucket[sentiment] += 1

        underlying_bucket = underlying_map[view.underlying]
        underlying_bucket["count"] += 1
        underlying_bucket["confidence_sum"] += confidence
        if sentiment in {"bullish", "bearish", "neutral"}:
            underlying_bucket[sentiment] += 1

        bank_bucket = bank_map[view.bank]
        bank_bucket["count"] += 1
        bank_bucket["confidence_sum"] += confidence
        if sentiment in {"bullish", "bearish", "neutral"}:
            bank_bucket[sentiment] += 1

    def build_rankings(source_map: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        items = []
        for label, payload in source_map.items():
            count = payload["count"]
            items.append(
                {
                    "label": label,
                    "count": count,
                    "share": _percentage(count, total_views),
                    "avg_confidence": round(payload["confidence_sum"] / count, 1) if count else 0.0,
                    "bullish": payload["bullish"],
                    "bearish": payload["bearish"],
                    "neutral": payload["neutral"],
                }
            )
        items.sort(key=lambda item: (-item["count"], -item["avg_confidence"], item["label"]))
        return items[:top_n]

    timeline = []
    for date_key in sorted(timeline_map.keys()):
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
                "share": _percentage(sentiment_counter[label], total_views),
            }
            for label in SENTIMENT_ORDER
        ],
        "confidence_breakdown": [
            {
                "label": label,
                "count": confidence_counter[label],
                "share": _percentage(confidence_counter[label], total_views),
            }
            for label, _, _ in CONFIDENCE_BUCKETS
        ],
        "top_underlyings": build_rankings(underlying_map),
        "top_banks": build_rankings(bank_map),
        "timeline": timeline,
        "recent_views": [_serialize_view(view) for view in sorted_recent[:recent_limit]],
    }


def _build_filter_options(views: List[UnderlyingView]) -> Dict[str, Any]:
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


def _run_tracked_job(action_name: str, runner: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
    with process_state_lock:
        if process_state["processing"]:
            raise HTTPException(status_code=409, detail="Processing already in progress")
        process_state["processing"] = True
        process_state["current_action"] = action_name

    try:
        result = runner()
        payload = {"action": action_name, **result}
        with process_state_lock:
            process_state["processing"] = False
            process_state["current_action"] = None
            process_state["last_run"] = dt.datetime.utcnow().isoformat() + "Z"
            process_state["last_result"] = payload
        return payload
    except Exception as exc:
        with process_state_lock:
            process_state["processing"] = False
            process_state["current_action"] = None
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/views", response_model=List[ViewResponse])
def get_views(
    underlying: Optional[str] = Query(None),
    bank: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("date"),
    sort_order: str = Query("desc"),
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    query = _build_views_query(
        db,
        underlying=underlying,
        bank=bank,
        sentiment=sentiment,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )
    query = _sort_query(query, sort_by, sort_order)
    views = query.limit(limit).all()
    return [_serialize_view(view) for view in views]


@app.get("/filters/meta")
def get_filter_meta(
    underlying: Optional[str] = Query(None),
    bank: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    views = _build_views_query(
        db,
        underlying=underlying,
        bank=bank,
        sentiment=sentiment,
        start_date=start_date,
        end_date=end_date,
        search=search,
    ).all()
    return _build_filter_options(views)


@app.get("/dashboard")
def get_dashboard(
    underlying: Optional[str] = Query(None),
    bank: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    recent_limit: int = Query(8, ge=1, le=30),
    top_n: int = Query(8, ge=3, le=20),
    db: Session = Depends(get_db),
):
    views = _build_views_query(
        db,
        underlying=underlying,
        bank=bank,
        sentiment=sentiment,
        start_date=start_date,
        end_date=end_date,
        search=search,
    ).all()
    filters_applied = {
        "underlying": underlying,
        "bank": bank,
        "sentiment": sentiment,
        "start_date": start_date,
        "end_date": end_date,
        "search": search,
    }
    return _build_dashboard_payload(
        views,
        filters_applied=filters_applied,
        recent_limit=recent_limit,
        top_n=top_n,
    )


@app.get("/status")
def get_status():
    with process_state_lock:
        return {
            "processing": process_state["processing"],
            "current_action": process_state["current_action"],
            "last_run": process_state["last_run"],
            "last_result": process_state["last_result"],
        }


@app.post("/process")
def process_range(request: ProcessRequest):
    return _run_tracked_job(
        "process_emails",
        lambda: process_email_range(
            start_date=request.start_date,
            end_date=request.end_date,
            refresh=request.refresh,
            provider=request.provider,
            model=request.model,
            strict=request.strict,
        ),
    )


@app.post("/backfill-missing-views")
def backfill_range(request: BackfillRequest):
    return _run_tracked_job(
        "backfill_missing_views",
        lambda: backfill_missing_views(
            start_date=request.start_date,
            end_date=request.end_date,
            provider=request.provider,
            model=request.model,
        ),
    )


if __name__ == "__main__":
    import uvicorn

    default_host = os.getenv("API_HOST", "127.0.0.1")
    default_port = _env_int("API_PORT", 8000)
    default_reload = _env_bool("API_RELOAD", False)
    default_workers = _env_int("API_WORKERS", 1)

    parser = argparse.ArgumentParser(description="Run the FastAPI app with optional uvicorn settings.")
    parser.add_argument("--host", default=default_host, help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=default_port, help="Port to bind the server to")
    parser.add_argument("--reload", action="store_true", default=default_reload, help="Enable auto-reload for development")
    parser.add_argument("--workers", type=int, default=default_workers, help="Number of worker processes")
    args = parser.parse_args()

    uvicorn.run(
        "api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
    )
