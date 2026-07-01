import argparse

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models import User
from app.services.access_profiles import limits_for_profile


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or update the first Apex Host admin user.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--name", default="Apex Admin")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        email = args.email.lower().strip()
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            user = User(email=email, full_name=args.name, hashed_password=get_password_hash(args.password))
            db.add(user)
        user.full_name = args.name
        user.hashed_password = get_password_hash(args.password)
        user.role = "admin"
        user.plan = "admin_internal"
        user.is_active = True
        user.limits = limits_for_profile("admin_internal")
        db.commit()
        print(f"Admin ready: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
