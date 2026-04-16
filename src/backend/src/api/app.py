from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backend.src.api.config import resolve_allowed_origins
from src.backend.src.api.routes import router
from src.backend.src.db.database import initialize_database


def create_app () -> FastAPI :
    """
    Build the FastAPI application with middleware and routes.
    """
    initialize_database()

    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolve_allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()
