"""
Admin Bootstrap Service for Nexus Studio.
Ensures secure initialization and verification of the primary studio ADMIN account.
"""
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.core.security import hash_password
from app.models.customer import Customer
from app.models.enums import UserRole
from app.models.user import User


async def bootstrap_admin_account(
    db: AsyncSession,
    email: Optional[str] = None,
    password: Optional[str] = None,
    force_update_password: bool = False,
) -> Tuple[Optional[User], bool]:
    """
    Idempotently bootstrap or verify the designated primary ADMIN user.
    Returns (user, created_flag).
    """
    target_email = (email or settings.ADMIN_EMAIL).lower().strip()
    target_password = password or settings.ADMIN_INITIAL_PASSWORD

    stmt = select(User).where(User.email == target_email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        changed = False
        if existing_user.role != UserRole.ADMIN:
            logger.info(f"Promoting existing user {target_email} to ADMIN role.")
            existing_user.role = UserRole.ADMIN
            changed = True

        if not existing_user.is_active:
            existing_user.is_active = True
            changed = True

        if target_password and force_update_password:
            logger.info(f"Updating password for admin user {target_email}.")
            existing_user.hashed_password = hash_password(target_password)
            changed = True

        if changed:
            await db.commit()
            await db.refresh(existing_user)

        return existing_user, False

    # User does not exist yet
    if not target_password:
        logger.info(
            f"Admin account ({target_email}) not present. "
            "To initialize, provide ADMIN_INITIAL_PASSWORD in the environment or run scripts/bootstrap_admin.py."
        )
        return None, False

    logger.info(f"Creating initial ADMIN user for {target_email}...")
    new_admin = User(
        email=target_email,
        hashed_password=hash_password(target_password),
        full_name="Nexus Studio Admin",
        phone=settings.STUDIO_PHONE,
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(new_admin)
    await db.flush()

    # Link customer/staff profile
    customer_profile = Customer(
        user_id=new_admin.id,
        full_name=new_admin.full_name,
        email=new_admin.email,
        phone=new_admin.phone or "",
        company_name="Nexus Studio HQ",
    )
    db.add(customer_profile)

    await db.commit()
    await db.refresh(new_admin)

    logger.info(f"Primary ADMIN account successfully bootstrapped for {target_email}.")
    return new_admin, True
