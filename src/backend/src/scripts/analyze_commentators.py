from __future__ import annotations

import sys

from collections import defaultdict
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[4]

if str(ROOT_DIR) not in sys.path :
    sys.path.insert(0, str(ROOT_DIR))

from src.backend.src.scripts.cli_utils import setup_environment

setup_environment(__file__, parent_levels=4)

from src.backend.src.db.database import SessionLocal, initialize_database
from src.backend.src.db.models import UnderlyingView


def analyze_commentators () -> None :
    """
    Rank banks/commentators by stored view count and average confidence.
    """
    initialize_database()
    db = SessionLocal()
    views = db.query(UnderlyingView).all()

    stats = defaultdict(lambda: {"count": 0, "total_confidence": 0, "sentiments": defaultdict(int)})

    for view in views :

        bank = view.bank
        
        stats[bank]["count"] += 1
        stats[bank]["total_confidence"] += view.confidence
        stats[bank]["sentiments"][view.sentiment] += 1

    ranked = []
    
    for bank, data in stats.items() :
        avg_confidence = data["total_confidence"] / data["count"] if data["count"] > 0 else 0
        ranked.append(
            {
                "bank": bank,
                "views_count": data["count"],
                "avg_confidence": round(avg_confidence, 2),
                "sentiments": dict(data["sentiments"]),
            }
        )

    ranked.sort(key=lambda x: (x["avg_confidence"], x["views_count"]), reverse=True)

    print("Top Market Commentators:")
    
    for i, commentator in enumerate(ranked[:10], 1) :
        print(f"{i}. {commentator['bank']}: {commentator['views_count']} views, Avg Confidence: {commentator['avg_confidence']}%")
        print(f"   Sentiments: {commentator['sentiments']}")

    db.close()


if __name__ == "__main__" :
    analyze_commentators()
