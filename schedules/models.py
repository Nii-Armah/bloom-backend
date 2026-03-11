from database import Base
from users.models import Professional

import datetime
import enum
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Schedule(Base):
    __tablename__ = 'schedules'

    class DayOfWeek(enum.Enum):
        MONDAY = 'monday'
        TUESDAY = 'tuesday'
        WEDNESDAY = 'wednesday'
        THURSDAY = 'thursday'
        FRIDAY = 'friday'
        SATURDAY = 'saturday'
        SUNDAY = 'sunday'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    professional_id: Mapped[UUID] = mapped_column(ForeignKey('professionals.id'))
    professional: Mapped['Professional'] = relationship('Professional')
    day_of_week: Mapped[DayOfWeek] = mapped_column()
    start_time: Mapped[datetime.time] = mapped_column()
    end_time: Mapped[datetime.time] = mapped_column()
    is_available: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(default=lambda: datetime.datetime.now(datetime.UTC))

    updated_at: Mapped[datetime.datetime] = mapped_column(
        default=lambda: datetime.datetime.now(datetime.UTC),
        onupdate=lambda: datetime.datetime.now(datetime.UTC),
    )

    __table_args__ = (
        CheckConstraint('start_time < end_time', name='check_start_before_end'),
        UniqueConstraint('professional_id', 'day_of_week', name='uq_day_of_week_for_professional'),
    )
