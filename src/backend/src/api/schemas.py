from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ViewResponse(BaseModel) :
    id : int
    email_id : Optional[int]
    underlying : str
    sentiment : str
    bank : str
    date : str
    rationale : str
    levels : str
    confidence : int


class ProcessRequest(BaseModel) :
    start_date : Optional[str] = None
    end_date : Optional[str] = None
    refresh : bool = False
    provider : Optional[str] = None
    model : Optional[str] = None
    strict : bool = False


class BackfillRequest(BaseModel) :
    start_date : Optional[str] = None
    end_date : Optional[str] = None
    provider : Optional[str] = None
    model : Optional[str] = None
