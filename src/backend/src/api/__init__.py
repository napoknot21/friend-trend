"""API package for the backend FastAPI application."""

from __future__ import annotations

from src.backend.src.api.app import app, create_app

__all__ = ["app", "create_app"]
