from database import Base
from users.models import Professional

import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Numeric, TEXT, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Service(Base):
    __tablename__ = 'services'

    def __init__(self, **kwargs):
        if not kwargs.get('professional_id') and not kwargs.get('professional'):
            raise ValueError('Service must have a professional.')
        super().__init__(**kwargs)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    professional_id: Mapped[UUID] = mapped_column(ForeignKey('professionals.id'), nullable=False)
    professional: Mapped['Professional'] = relationship('Professional', back_populates='services')
    name: Mapped[str] = mapped_column(max_length=200)
    description: Mapped[str] = mapped_column(TEXT, default='')
    price: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2))
    duration: Mapped[int] = mapped_column() # in minutes
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(default=lambda: datetime.datetime.now(datetime.UTC))

    updated_at: Mapped[datetime.datetime] = mapped_column(
        default=lambda: datetime.datetime.now(datetime.UTC),
        onupdate=lambda: datetime.datetime.now(datetime.UTC),
    )

    __table_args__ = (
        UniqueConstraint('professional_id', 'name', name='uq_professional_service_name'),
    )