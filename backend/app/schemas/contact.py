from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

_EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,255}\.[^@\s]{2,}$")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class ContactRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=320)
    message: str = Field(min_length=10, max_length=2000)
    # Honeypot: hidden in the UI. Real visitors leave it empty; simple bots fill it in.
    website: str = Field(default="", max_length=200)

    @field_validator("name", "message")
    @classmethod
    def _clean_text(cls, v: str) -> str:
        v = _CONTROL.sub("", v).strip()
        if not v:
            raise ValueError("must not be blank")
        return v

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL.match(v):
            raise ValueError("must be a valid email address")
        return v


class ContactResponse(BaseModel):
    status: Literal["received"]
