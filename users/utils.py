import datetime
import os
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from dotenv import load_dotenv
from jose import jwt, JWTError


load_dotenv()


SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS'))


hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return hasher.hash(password)


def verify_password(hashed_password: str, password: str,) -> bool:
    try:
        return hasher.verify(hashed_password, password)
    except VerifyMismatchError:
        return False


def create_token(data: dict, expires_delta: datetime.timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    to_encode.update({'exp': expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def generate_auth_tokens(subject: str | Any) -> dict:
    """Creates authentication token pair"""
    access_delta = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_delta = datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    return {
        'access_token': create_token({'sub': str(subject), 'type': 'access'}, access_delta),
        'refresh_token': create_token({'sub': str(subject), 'type': 'refresh'}, refresh_delta),
        'token_type': 'bearer'
    }


def decode_token(token: str) -> dict | None:
    """
    Decodes a JWT and returns the payload dictionary.
    Returns None if the token is invalid, expired, or tampered with.
    """

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
