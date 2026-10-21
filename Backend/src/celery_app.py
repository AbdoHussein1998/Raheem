"""Celery worker entry point (run from src/ on PYTHONPATH)."""
from dotenv import load_dotenv

load_dotenv("src/.env")
load_dotenv()

from Celery.Config.celery_defination import celery_app

__all__ = ["celery_app"]
