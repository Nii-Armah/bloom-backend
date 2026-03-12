from .models import Service

import decimal

from pydantic import BaseModel, Field, ValidationInfo, field_validator
from sqlalchemy import exists, func


class ServiceSchema(BaseModel):
    name: str
    description: str = ''
    price: decimal.Decimal = Field(max_digits=10, decimal_places=2, gt=0)
    duration: int = Field(gt=0)

    @field_validator('name')
    @classmethod
    def validate_name(cls, name, info: ValidationInfo):
        db = info.context.get('db_session')
        professional = info.context.get('professional')

        name_exists = db.query(exists().where(
            Service.professional_id == professional.id,
            func.lower(Service.name) == name.lower()
        )).scalar()

        if name_exists:
            raise ValueError('Professional has a service by the given name')

        return name
