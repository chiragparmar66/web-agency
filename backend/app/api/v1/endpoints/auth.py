from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.auth import (
    PasswordChangeRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.schemas.common import APIResponse
from app.schemas.customer import CustomerResponse, CustomerUpdate
from app.schemas.user import UserProfileResponse, UserUpdate
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=APIResponse[TokenResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new customer account",
)
async def register(
    register_in: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    token_response = await AuthService.register_user(db, register_in)
    return APIResponse(
        success=True,
        message="Account registered successfully.",
        data=token_response,
    )


@router.post(
    "/login",
    response_model=APIResponse[TokenResponse],
    summary="Authenticate and receive JWT tokens",
)
async def login(
    login_in: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    token_response = await AuthService.authenticate_user(db, login_in)
    return APIResponse(
        success=True,
        message="Authentication successful.",
        data=token_response,
    )


@router.post(
    "/refresh",
    response_model=APIResponse[TokenResponse],
    summary="Refresh access token using refresh token",
)
async def refresh_token(
    refresh_in: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    token_response = await AuthService.refresh_user_token(db, refresh_in.refresh_token)
    return APIResponse(
        success=True,
        message="Token refreshed successfully.",
        data=token_response,
    )


@router.get(
    "/me",
    response_model=APIResponse[UserProfileResponse],
    summary="Get current user profile and customer details",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
):
    profile = UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        customer_profile=CustomerResponse.model_validate(current_user.customer_profile)
        if current_user.customer_profile
        else None,
    )
    return APIResponse(
        success=True,
        message="User profile retrieved.",
        data=profile,
    )


@router.put(
    "/me",
    response_model=APIResponse[UserProfileResponse],
    summary="Update current user and customer profile",
)
async def update_me(
    user_update: UserUpdate,
    customer_update: CustomerUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.phone is not None:
        current_user.phone = user_update.phone

    if current_user.customer_profile:
        for field, value in customer_update.model_dump(exclude_unset=True).items():
            setattr(current_user.customer_profile, field, value)

    await db.commit()
    await db.refresh(current_user)

    profile = UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        customer_profile=CustomerResponse.model_validate(current_user.customer_profile)
        if current_user.customer_profile
        else None,
    )
    return APIResponse(
        success=True,
        message="Profile updated successfully.",
        data=profile,
    )


@router.post(
    "/change-password",
    response_model=APIResponse[dict],
    summary="Change user account password",
)
async def change_password(
    pwd_in: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from app.core.exceptions import StudioBaseException
    from app.core.security import hash_password, verify_password

    if not verify_password(pwd_in.current_password, current_user.hashed_password):
        raise StudioBaseException(
            message="Incorrect current password.",
            code="INVALID_PASSWORD",
        )

    current_user.hashed_password = hash_password(pwd_in.new_password)
    await db.commit()

    return APIResponse(
        success=True,
        message="Password updated successfully.",
        data={"updated": True},
    )

