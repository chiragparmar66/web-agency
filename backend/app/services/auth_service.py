from datetime import datetime, timezone
from typing import Optional
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import StudioBaseException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.customer import Customer
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.schemas.user import UserPublicResponse


class AuthService:
    @staticmethod
    async def register_user(
        db: AsyncSession,
        register_in: UserRegisterRequest,
    ) -> TokenResponse:
        # Check if email already registered
        stmt = select(User).where(User.email == register_in.email.lower().strip())
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise StudioBaseException(
                message="An account with this email already exists.",
                code="EMAIL_ALREADY_EXISTS",
            )

        # Hash password securely
        hashed_pwd = hash_password(register_in.password)

        # Force role to CUSTOMER during public registration (prevent privilege escalation)
        new_user = User(
            email=register_in.email.lower().strip(),
            hashed_password=hashed_pwd,
            full_name=register_in.full_name.strip(),
            phone=register_in.phone.strip() if register_in.phone else None,
            role=UserRole.CUSTOMER,
            is_active=True,
        )
        db.add(new_user)
        await db.flush()

        # Check if an existing Customer profile with this phone or email exists (e.g. from lead intake)
        customer_stmt = select(Customer).where(
            (Customer.email == new_user.email)
            | (Customer.phone == (new_user.phone or "non_matching_phone"))
        )
        cust_res = await db.execute(customer_stmt)
        existing_customer = cust_res.scalar_one_or_none()

        if existing_customer and existing_customer.user_id is None:
            # Link existing customer lead to this new user account
            existing_customer.user_id = new_user.id
            if register_in.company_name:
                existing_customer.company_name = register_in.company_name
            if register_in.city:
                existing_customer.city = register_in.city
        else:
            # Create fresh customer profile
            new_customer = Customer(
                user_id=new_user.id,
                full_name=new_user.full_name,
                email=new_user.email,
                phone=new_user.phone or "",
                company_name=register_in.company_name,
                business_type=register_in.business_type,
                city=register_in.city,
            )
            db.add(new_customer)

        await db.commit()
        await db.refresh(new_user)

        # Generate JWT tokens
        token_payload = {"sub": str(new_user.id), "role": new_user.role.value}
        access_token = create_access_token(subject=str(new_user.id))
        refresh_tok = create_refresh_token(subject=str(new_user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_tok,
            token_type="Bearer",
            expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserPublicResponse.model_validate(new_user),
        )

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        login_in: UserLoginRequest,
    ) -> TokenResponse:
        stmt = (
            select(User)
            .options(selectinload(User.customer_profile))
            .where(User.email == login_in.email.lower().strip())
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(login_in.password, user.hashed_password):
            raise StudioBaseException(
                message="Invalid email or password.",
                code="INVALID_CREDENTIALS",
            )

        if not user.is_active:
            raise StudioBaseException(
                message="User account is deactivated. Please contact support.",
                code="ACCOUNT_DEACTIVATED",
            )

        access_token = create_access_token(subject=str(user.id))
        refresh_tok = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_tok,
            token_type="Bearer",
            expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserPublicResponse.model_validate(user),
        )

    @staticmethod
    async def refresh_user_token(
        db: AsyncSession,
        refresh_token_str: str,
    ) -> TokenResponse:
        try:
            payload = jwt.decode(
                refresh_token_str,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            if payload.get("type") != "refresh":
                raise StudioBaseException(
                    message="Invalid token type.",
                    code="INVALID_TOKEN",
                )
            user_id = payload.get("sub")
            if not user_id:
                raise StudioBaseException(
                    message="Token missing subject.",
                    code="INVALID_TOKEN",
                )
        except JWTError:
            raise StudioBaseException(
                message="Refresh token has expired or is invalid.",
                code="TOKEN_EXPIRED",
            )

        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise StudioBaseException(
                message="User not found or deactivated.",
                code="USER_NOT_FOUND",
            )

        new_access = create_access_token(subject=str(user.id))
        new_refresh = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            token_type="Bearer",
            expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserPublicResponse.model_validate(user),
        )
