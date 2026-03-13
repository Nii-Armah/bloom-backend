from database import Base
from services.models import Service
from users.models import Client, Professional

import datetime
import enum
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Booking(Base):
    __tablename__ = 'bookings'

    class Status(enum.Enum):
        CONFIRMED = 'confirmed'
        COMPLETED = 'completed'
        CANCELLED = 'cancelled'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    client_id: Mapped[UUID] = mapped_column(ForeignKey('clients.id'))
    client: Mapped['Client'] = relationship('Client')
    professional_id: Mapped[UUID] = mapped_column(ForeignKey('professionals.id'))
    professional: Mapped['Professional'] = relationship('Professional')
    service_id: Mapped[UUID] = mapped_column(ForeignKey('services.id'))
    service: Mapped['Service'] = relationship('Service')
    start: Mapped[datetime.datetime] = mapped_column()
    end: Mapped[datetime.datetime] = mapped_column()
    status: Mapped[Status] = mapped_column(default=Status.CONFIRMED)
    created_at: Mapped[datetime.datetime] = mapped_column(default=lambda: datetime.datetime.now(datetime.UTC))

    updated_at: Mapped[datetime.datetime] = mapped_column(
        default=lambda: datetime.datetime.now(datetime.UTC),
        onupdate=lambda: datetime.datetime.now(datetime.UTC),
    )

    __table_args__ = (
        CheckConstraint('start < end', name='start_time_should_precede_end_time'),
    )
