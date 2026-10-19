"""Create an administrator locally; passwords are entered privately."""
import argparse
from getpass import getpass
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydantic import EmailStr, TypeAdapter
from app.config import Settings
from app.repositories.users import UserRepository
from app.services.auth import hash_password


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    email = str(TypeAdapter(EmailStr).validate_python(args.email)).lower()
    users = UserRepository(Settings().data_dir / "app.sqlite3")
    if users.by_email(email):
        parser.error("An account with this email already exists. Use a separate administrator email.")
    password = getpass("Password (8–128 characters): ")
    if not 8 <= len(password) <= 128 or password != getpass("Confirm password: "):
        parser.error("Passwords must match and be 8–128 characters.")
    users.create(email, hash_password(password), role="admin")
    print(f"Administrator created: {email}")


if __name__ == "__main__":
    main()
