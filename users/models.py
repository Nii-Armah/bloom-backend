from .utils import hash_password
from database import Base

import datetime
import enum
from uuid import UUID, uuid4

from sqlalchemy import TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Client(Base):
    __tablename__ = 'clients'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    full_name: Mapped[str] = mapped_column(max_length=200)
    email: Mapped[str] = mapped_column(max_length=100, unique=True, index=True)
    contact_number: Mapped[str] = mapped_column(max_length=20, default='')
    password: Mapped[str] = mapped_column(max_length=125)
    created_at: Mapped[datetime.datetime] = mapped_column(default=lambda: datetime.datetime.now(datetime.UTC))

    updated_at: Mapped[datetime.datetime] = mapped_column(
        default=lambda: datetime.datetime.now(datetime.UTC),
        onupdate=lambda: datetime.datetime.now(datetime.UTC),
    )

    def __init__(self, **kwargs):
        if kwargs.get('password'):
            kwargs['password'] = hash_password(kwargs.get('password'))
        super().__init__(**kwargs)


class Professional(Base):
    __tablename__ = 'professionals'

    class Specialty(str, enum.Enum):
        HAIR_STYLING = 'hair_styling'
        HAIR_COLORING = 'hair_coloring'
        MAKEUP_ARTISTRY = 'makeup_artistry'
        SKINCARE = 'skincare'
        LASH_SERVICES = 'lash_services'
        NAIL_SERVICES = 'nail_services'

    def __init__(self, **kwargs):
        if kwargs.get('password'):
            kwargs['password'] = hash_password(kwargs.get('password'))
        super().__init__(**kwargs)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    full_name: Mapped[str] = mapped_column(max_length=200)
    email: Mapped[str] = mapped_column(max_length=100, unique=True, index=True)
    bio: Mapped[str] = mapped_column(TEXT, default='')
    is_verified: Mapped[bool] = mapped_column(default=False)
    specialty: Mapped[Specialty] = mapped_column()
    password: Mapped[str] = mapped_column(max_length=125)
    created_at: Mapped[datetime.datetime] = mapped_column(default=lambda: datetime.datetime.now(datetime.UTC))
    services: Mapped[list['Service']] = relationship('Service', back_populates='professional')

    updated_at: Mapped[datetime.datetime] = mapped_column(
        default=lambda: datetime.datetime.now(datetime.UTC),
        onupdate=lambda: datetime.datetime.now(datetime.UTC),
    )


from services.models import Service