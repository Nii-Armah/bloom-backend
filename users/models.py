from .utils import hash_password
from database import Base

import datetime
from uuid import UUID, uuid4

from sqlalchemy.orm import Mapped, mapped_column


class Client(Base):
    __tablename__ = 'clients'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    full_name: Mapped[str] = mapped_column(max_length=200)
    email: Mapped[str] = mapped_column(max_length=100, unique=True, index=True)
    contact_number: Mapped[str] = mapped_column(max_length=20, nullable=True, default='')
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
