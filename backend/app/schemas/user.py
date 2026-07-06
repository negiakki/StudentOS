"""User profile API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str | None = None
    college: str | None = None
    degree: str | None = None
    onboarding_completed: bool
    created_at: datetime
    updated_at: datetime


class OnboardingRequest(BaseModel):
    full_name: str | None = None
    college: str | None = None
    degree: str | None = None
