"""Session service initialization and lifecycle management."""

import logging
from typing import Optional
from google.adk.sessions import BaseSessionService, InMemorySessionService
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from ...config.settings import settings

logger = logging.getLogger("patient_onboarding.session")


def get_session_service(backend_type: Optional[str] = None) -> BaseSessionService:
    """Factory function returning configured ADK SessionService.

    Args:
        backend_type: Override backend: 'memory' or 'sqlite'.

    Returns:
        Configured BaseSessionService instance.
    """
    backend = backend_type or settings.session_backend

    if backend == "sqlite":
        logger.info(f"Initializing SqliteSessionService with database at {settings.sqlite_db_path}")
        return SqliteSessionService(db_path=settings.sqlite_db_path)
    
    # Default to InMemorySessionService for fast test execution and lightweight dev
    logger.info("Initializing InMemorySessionService")
    return InMemorySessionService()
