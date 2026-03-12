from .models import Client, Professional
from pydantic import BaseModel, ConfigDict, EmailStr, ValidationInfo, field_validator, model_validator

from typing import Self
from uuid import UUID

from sqlalchemy import exists
from sqlalchemy.orm import Session


class ClientOut(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    contact_number: str = ''

    model_config = ConfigDict(from_attributes=True)

class ProfessionalOut(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    bio: str = ''
    is_verified: bool = False
    specialty: Professional.Specialty


    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'


class ClientAuthResponse(BaseModel):
    user: ClientOut
    tokens: Token


class ProfessionalAuthResponse(BaseModel):
    user: ProfessionalOut
    tokens: Token


class ClientSchema(BaseModel):
    full_name: str
    email: EmailStr
    contact_number: str = ''
    password: str
    password2: str

    @field_validator('email')
    @classmethod
    def check_email(cls, email, info: ValidationInfo) -> str:
        db: Session = info.context.get('db_session')
        if db.query(exists().where(Client.email == email)).scalar():
            raise ValueError('Email already exists')

        return email

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, password):
        if len(password) < 8:
            raise ValueError('Password should have a minimum of 8 characters')
        return password

    @model_validator(mode='after')
    def check_passwords_match(self) -> Self:
        if self.password != self.password2:
            raise ValueError('Passwords do not match')

        return self

    @model_validator(mode='after')
    def cleanup(self) -> Self:
        del self.password2
        return self


class ProfessionalSchema(BaseModel):
    full_name: str
    email: EmailStr
    bio: str = ''
    specialty: Professional.Specialty
    password: str
    password2: str

    @field_validator('email')
    @classmethod
    def check_email(cls, email, info: ValidationInfo) -> str:
        db: Session = info.context.get('db_session')
        if db.query(exists().where(Professional.email == email)).scalar():
            raise ValueError('Email already exists')

        return email

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, password):
        if len(password) < 8:
            raise ValueError('Password should have a minimum of 8 characters')
        return password

    @model_validator(mode='after')
    def check_passwords_match(self) -> Self:
        if self.password != self.password2:
            raise ValueError('Passwords do not match')

        return self

    @model_validator(mode='after')
    def cleanup(self) -> Self:
        del self.password2
        return self


class LoginSchema(BaseModel):
    email: EmailStr
    password: str