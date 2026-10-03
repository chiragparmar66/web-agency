"""
CLI script to bootstrap the Nexus Studio initial ADMIN account.
Usage:
    python scripts/bootstrap_admin.py --password "YourAdminPasswordHere"
    python scripts/bootstrap_admin.py --email "chiragparmar5768@gmail.com" --password "YourAdminPasswordHere"
"""
import argparse
import asyncio
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.db.session import async_session_factory
from app.services.admin_bootstrap import bootstrap_admin_account


async def main():
    parser = argparse.ArgumentParser(description="Bootstrap Nexus Studio primary administrator account.")
    parser.add_argument("--email", default=settings.ADMIN_EMAIL, help="Admin email address")
    parser.add_argument("--password", default=settings.ADMIN_INITIAL_PASSWORD, help="Initial admin password")
    parser.add_argument("--force-update-password", action="store_true", help="Force update password if user exists")

    args = parser.parse_args()

    if not args.password:
        print("ERROR: Admin password must be provided via --password or ADMIN_INITIAL_PASSWORD env var.")
        sys.exit(1)

    async with async_session_factory() as session:
        user, created = await bootstrap_admin_account(
            db=session,
            email=args.email,
            password=args.password,
            force_update_password=args.force_update_password,
        )

    if user:
        action = "Created new" if created else "Verified/Updated existing"
        print(f"SUCCESS: {action} admin account:")
        print(f"  ID:    {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Role:  {user.role.value}")
        print(f"  Name:  {user.full_name}")
    else:
        print("ERROR: Failed to bootstrap admin account.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
