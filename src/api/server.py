from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.db.database import get_db
from src.db.models import Email, UnderlyingView
from typing import List, Dict, Any
from collections import defaultdict
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Trend Classifier API")

# Setup CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    """
    Returns aggregated sentiment data for the top underlyings.
    """
    views = db.query(UnderlyingView).all()
    
    # Simple aggregation
    underlying_stats = defaultdict(lambda: {"bullish": 0, "bearish": 0, "neutral": 0, "total": 0})
    for view in views:
        u = view.underlying
        s = view.sentiment
        if s in ["bullish", "bearish", "neutral"]:
            underlying_stats[u][s] += 1
            underlying_stats[u]["total"] += 1
            
    # Convert to list and calculate consensus
    response = []
    for u, stats in underlying_stats.items():
        if stats["total"] > 0:
            # simple score: bullish = +1, bearish = -1. Neutral = 0.
            score = (stats["bullish"] - stats["bearish"]) / stats["total"]
            consensus = "bullish" if score > 0.3 else "bearish" if score < -0.3 else "neutral"
            
            response.append({
                "underlying": u,
                "stats": stats,
                "score": score,
                "consensus": consensus
            })
            
    # Sort by total conviction (most talked about)
    response.sort(key=lambda x: x["stats"]["total"], reverse=True)
    return response

@app.get("/api/underlying/{ticker}")
def get_underlying_details(ticker: str, db: Session = Depends(get_db)):
    """
    Returns detailed views for a specific underlying.
    """
    views = db.query(UnderlyingView).filter(UnderlyingView.underlying.ilike(ticker)).order_by(UnderlyingView.date.desc()).all()
    
    result = []
    for v in views:
        result.append({
            "id": v.id,
            "bank": v.bank,
            "sentiment": v.sentiment,
            "date": v.date,
            "rationale": v.rationale,
            "levels": v.levels,
            "email_subject": v.email.subject if v.email else ""
        })
    return result

@app.get("/api/sources")
def get_sources(db: Session = Depends(get_db)):
    """
    Returns a list of commentators and the volume of their calls.
    """
    views = db.query(UnderlyingView).all()
    
    bank_stats = defaultdict(lambda: {"total_calls": 0, "underlyings_covered": set()})
    for view in views:
        b = view.bank
        bank_stats[b]["total_calls"] += 1
        bank_stats[b]["underlyings_covered"].add(view.underlying)
        
    response = []
    for b, stats in bank_stats.items():
        response.append({
            "bank": b,
            "total_calls": stats["total_calls"],
            "unique_underlyings_covered": len(stats["underlyings_covered"])
        })
        
    response.sort(key=lambda x: x["total_calls"], reverse=True)
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.server:app", host="127.0.0.1", port=8000, reload=True)
