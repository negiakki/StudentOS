"""User profile endpoints.

Demonstrates the full request path: authenticated request (JWT) → service
(business logic) → repository (data access) → database. Every operation is
scoped to the current user derived from the verified token.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import CurrentUserDep
from app.database.session import get_db
from app.schemas.user import OnboardingRequest, UserProfile
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

DbDep = Annotated[Session, Depends(get_db)]


@router.get("/me", response_model=UserProfile)
def get_my_profile(current_user: CurrentUserDep, db: DbDep) -> UserProfile:
    """Return the current user's StudentOS profile, creating it on first sign-in."""
    user = UserService(db).get_or_create_profile(current_user)
    return UserProfile.model_validate(user)


@router.post("/me/onboarding", response_model=UserProfile)
def complete_onboarding(
    payload: OnboardingRequest, current_user: CurrentUserDep, db: DbDep
) -> UserProfile:
    """Save onboarding details and mark onboarding as complete."""
    user = UserService(db).complete_onboarding(
        current_user,
        full_name=payload.full_name,
        college=payload.college,
        degree=payload.degree,
    )
    return UserProfile.model_validate(user)
