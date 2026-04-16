from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.backend.src.api.schemas import BackfillRequest, ProcessRequest, ViewResponse
from src.backend.src.api.services import (
    build_dashboard_payload,
    build_filter_options,
    build_views_query,
    serialize_view,
    sort_query,
)
from src.backend.src.api.state import get_process_status, run_tracked_job
from src.backend.src.db.database import get_db
from src.backend.src.processor import backfill_missing_views, process_email_range


router = APIRouter()


@router.get("/views", response_model=List[ViewResponse])
def get_views(
    underlying : Optional[str] = Query(None),
    bank : Optional[str] = Query(None),
    sentiment : Optional[str] = Query(None),
    start_date : Optional[str] = Query(None),
    end_date : Optional[str] = Query(None),
    search : Optional[str] = Query(None),
    sort_by : str = Query("date"),
    sort_order : str = Query("desc"),
    limit : int = Query(500, ge=1, le=5000),
    db : Session = Depends(get_db),
) :
    """
    Return stored views after applying filters and sorting.
    """
    query = build_views_query(
        db,
        underlying=underlying,
        bank=bank,
        sentiment=sentiment,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )
    query = sort_query(query, sort_by, sort_order)
    views = query.limit(limit).all()
    return [serialize_view(view) for view in views]


@router.get("/filters/meta")
def get_filter_meta(
    underlying : Optional[str] = Query(None),
    bank : Optional[str] = Query(None),
    sentiment : Optional[str] = Query(None),
    start_date : Optional[str] = Query(None),
    end_date : Optional[str] = Query(None),
    search : Optional[str] = Query(None),
    db : Session = Depends(get_db),
) :
    """
    Return available filter options for the current slice of data.
    """
    views = build_views_query(
        db,
        underlying=underlying,
        bank=bank,
        sentiment=sentiment,
        start_date=start_date,
        end_date=end_date,
        search=search,
    ).all()
    return build_filter_options(views)


@router.get("/dashboard")
def get_dashboard(
    underlying : Optional[str] = Query(None),
    bank : Optional[str] = Query(None),
    sentiment : Optional[str] = Query(None),
    start_date : Optional[str] = Query(None),
    end_date : Optional[str] = Query(None),
    search : Optional[str] = Query(None),
    recent_limit : int = Query(8, ge=1, le=30),
    top_n : int = Query(8, ge=3, le=20),
    db : Session = Depends(get_db),
) :
    """
    Return the dashboard payload for the current filters.
    """
    views = build_views_query(
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
    return build_dashboard_payload(
        views,
        filters_applied=filters_applied,
        recent_limit=recent_limit,
        top_n=top_n,
    )


@router.get("/status")
def get_status() :
    """
    Return the current processing status.
    """
    return get_process_status()


@router.post("/process")
def process_range(request : ProcessRequest) :
    """
    Trigger a range processing job.
    """
    return run_tracked_job(
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


@router.post("/backfill-missing-views")
def backfill_range(request : BackfillRequest) :
    """
    Trigger a backfill job for saved emails missing views.
    """
    return run_tracked_job(
        "backfill_missing_views",
        lambda: backfill_missing_views(
            start_date=request.start_date,
            end_date=request.end_date,
            provider=request.provider,
            model=request.model,
        ),
    )
