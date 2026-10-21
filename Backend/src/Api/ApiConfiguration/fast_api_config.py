"""Backward-compatible import path; use api_configurations and api_services."""
from .api_configurations import create_app, create_lifespan
from .api_services import ApplicationServices

__all__ = ["create_app", "create_lifespan", "ApplicationServices"]
