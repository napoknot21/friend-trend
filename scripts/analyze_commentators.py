#!/usr/bin/env python3
"""
Analyze market commentators based on stored views.
Ranks banks by average confidence, number of views, etc.
"""

from collections import defaultdict
from src.db.database import SessionLocal
from src.db.models import UnderlyingView

def analyze_commentators():
    db = SessionLocal()
    views = db.query(UnderlyingView).all()

    stats = defaultdict(lambda: {"count": 0, "total_confidence": 0, "sentiments": defaultdict(int)})

    for view in views:
        bank = view.bank
        stats[bank]["count"] += 1
        stats[bank]["total_confidence"] += view.confidence
        stats[bank]["sentiments"][view.sentiment] += 1

    # Compute averages and rank
    ranked = []
    for bank, data in stats.items():
        avg_confidence = data["total_confidence"] / data["count"] if data["count"] > 0 else 0
        ranked.append({
            "bank": bank,
            "views_count": data["count"],
            "avg_confidence": round(avg_confidence, 2),
            "sentiments": dict(data["sentiments"])
        })

    ranked.sort(key=lambda x: (x["avg_confidence"], x["views_count"]), reverse=True)

    print("Top Market Commentators:")
    for i, commentator in enumerate(ranked[:10], 1):  # Top 10
        print(f"{i}. {commentator['bank']}: {commentator['views_count']} views, Avg Confidence: {commentator['avg_confidence']}%")
        print(f"   Sentiments: {commentator['sentiments']}")

    db.close()

if __name__ == "__main__":
    analyze_commentators()