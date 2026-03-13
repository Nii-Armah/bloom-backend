from database import get_session
from users.models import Client, Professional
from users.utils import decode_token

from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='api/v1/auth/login')


class AuthException(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_session)):
    try:
        payload = decode_token(token)
        user_id = payload.get('sub')
        if user_id is None:
            raise AuthException(401, 'Could not validate credentials')
    except JWTError:
        raise AuthException(401, 'Could not validate credentials')

    try:
        user_id = UUID(user_id)
    except ValueError:
        raise AuthException(401, 'Invalid token format')

    user = db.query(Client).filter(Client.id == user_id).first()
    if user is None:
        user = db.query(Professional).filter(Professional.id == user_id).first()

    if user is None:
        raise AuthException(401, 'User not found')

    return user


def get_current_client(user = Depends(get_current_user)) -> Client:
    if not isinstance(user, Client):
        raise AuthException(403, 'Access denied. Client account required.')
    return user


def get_current_professional(user = Depends(get_current_user)) -> Professional:
    if not isinstance(user, Professional):
        raise AuthException(403, 'Access denied. Professional account required.')
    return user
