from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return hasher.hash(password)


def verify_password(hashed_password: str, password: str,) -> bool:
    try:
        return hasher.verify(hashed_password, password)
    except VerifyMismatchError:
        return False
