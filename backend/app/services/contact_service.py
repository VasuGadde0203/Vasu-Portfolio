"""Stores contact-form messages in the application's PostgreSQL database."""

from __future__ import annotations

import logging
from typing import Protocol

from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.db.models import ContactMessage
from app.db.session import open_session
from app.services.errors import ServiceError

log = logging.getLogger(__name__)


class ContactStore(Protocol):
    def save(self, document: dict) -> None: ...


class PostgresContactStore:
    def save(self, document: dict) -> None:
        try:
            with open_session() as session:
                session.add(ContactMessage(**document))
                session.commit()
        except SQLAlchemyError as exc:
            log.error("Contact message could not be stored (%s)", type(exc).__name__)
            raise ServiceError("contact_unavailable",
                               "Your message couldn't be sent right now. Please email me directly.", 503) from exc


def build_contact_store(settings: Settings) -> ContactStore:
    return PostgresContactStore()
