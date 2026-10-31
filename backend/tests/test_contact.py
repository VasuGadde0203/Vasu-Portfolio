"""Contact form: validation, honeypot, rate limiting and storage (fake store for most tests, plus a
real PostgreSQL round trip)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_engine
from app.main import create_app
from app.schemas.contact import ContactRequest
from app.services.errors import ServiceError
from tests.conftest import FakeAI
from tests.test_integration_db import migrated_database  # noqa: F401  (fixture: real schema)

pytestmark = pytest.mark.integration
GOOD = {"name": "Asha Rao", "email": "Asha@Example.com", "message": "Hi Vasu, we'd like to talk about a role."}


class FakeStore:
    def __init__(self) -> None:
        self.saved: list[dict] = []

    def save(self, document: dict) -> None:
        self.saved.append(document)


@pytest.fixture
def client(migrated_database, settings):  # noqa: F811
    with Session(get_engine()) as s:
        s.execute(text("TRUNCATE rate_limit_counters"))
        s.commit()
    store = FakeStore()
    with TestClient(create_app(settings, FakeAI(), contact_store=store)) as c:
        c.store = store  # type: ignore[attr-defined]
        yield c


def test_valid_message_is_stored_with_hashed_client_only(client):
    r = client.post("/api/contact", json=GOOD)
    assert r.status_code == 200 and r.json() == {"status": "received"}
    (doc,) = client.store.saved
    assert doc["email"] == "asha@example.com" and doc["name"] == "Asha Rao"
    assert len(doc["client"]) == 32 and "testclient" not in doc["client"]  # hashed, not the raw address


@pytest.mark.parametrize("patch", [
    {"name": ""}, {"name": "   "}, {"email": "not-an-email"}, {"email": "a@b"}, {"message": "short"},
    {"message": "x" * 2001}, {"name": "n" * 101},
])
def test_invalid_input_is_rejected_and_not_stored(client, patch):
    assert client.post("/api/contact", json={**GOOD, **patch}).status_code == 422
    assert client.store.saved == []


def test_unknown_fields_are_rejected(client):
    assert client.post("/api/contact", json={**GOOD, "admin": True}).status_code == 422


def test_honeypot_returns_success_but_stores_nothing(client):
    r = client.post("/api/contact", json={**GOOD, "website": "http://spam.example"})
    assert r.status_code == 200 and client.store.saved == []


def test_rate_limit_per_client(client, settings):
    client.app.dependency_overrides[get_settings] = lambda: settings.model_copy(update={"contact_rate_limit_per_hour": 2})
    codes = [client.post("/api/contact", json=GOOD).status_code for _ in range(4)]
    client.app.dependency_overrides.clear()
    assert codes == [200, 200, 429, 429] and len(client.store.saved) == 2


def test_storage_failure_returns_safe_503(migrated_database, settings):  # noqa: F811
    class BrokenStore:
        def save(self, document: dict) -> None:
            raise ServiceError("contact_unavailable", "Your message couldn't be sent right now.", 503)

    with TestClient(create_app(settings, FakeAI(), contact_store=BrokenStore())) as c:
        r = c.post("/api/contact", json=GOOD)
        assert r.status_code == 503 and r.json()["error"]["code"] == "contact_unavailable"


def test_control_characters_are_stripped():
    req = ContactRequest(**{**GOOD, "message": "Hello\x00 there\x07, long enough"})
    assert "\x00" not in req.message and "\x07" not in req.message


def test_default_store_writes_to_postgres(migrated_database, settings):  # noqa: F811
    with Session(get_engine()) as db:
        db.execute(text("TRUNCATE rate_limit_counters, contact_messages"))
        db.commit()
    with TestClient(create_app(settings, FakeAI())) as c:  # no store passed: the real PostgreSQL store
        assert c.post("/api/contact", json=GOOD).status_code == 200
    with Session(get_engine()) as db:
        rows = db.execute(text("SELECT name, email, message, client, created_at FROM contact_messages")).all()
    assert len(rows) == 1
    name, email, message, client_hash, created_at = rows[0]
    assert (name, email) == ("Asha Rao", "asha@example.com") and message == GOOD["message"]
    assert len(client_hash) == 32 and created_at is not None
