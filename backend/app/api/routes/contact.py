from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool

from app.core.config import Settings, get_settings
from app.core.security import client_key, enforce_contact_rate_limit
from app.schemas.contact import ContactRequest, ContactResponse
from app.services.contact_service import ContactStore
from app.services.errors import ServiceError

router = APIRouter(tags=["contact"])


@router.post("/contact", response_model=ContactResponse, dependencies=[Depends(enforce_contact_rate_limit)])
async def submit_contact(
    body: ContactRequest, request: Request, settings: Settings = Depends(get_settings)
) -> ContactResponse:
    if body.website:  # honeypot tripped: pretend success, store nothing
        return ContactResponse(status="received")
    store: ContactStore | None = request.app.state.contact_store
    if store is None:
        raise ServiceError("contact_unavailable",
                           "The contact form isn't available right now. Please email me directly.", 503)
    await run_in_threadpool(store.save, {
        "name": body.name,
        "email": body.email,
        "message": body.message,
        "client": client_key(request, settings),  # hashed IP only; never the raw address
    })
    return ContactResponse(status="received")
