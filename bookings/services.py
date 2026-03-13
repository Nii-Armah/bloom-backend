from .models import Booking
from schedules.models import Schedule
from users.models import Professional

import datetime

from sqlalchemy.orm import Session

class BookingService:
    @staticmethod
    def slot_fits_schedule(schedule: Schedule, start: datetime.datetime, end: datetime.datetime) -> bool:
        start_time = start.time()
        end_time = end.time()

        return schedule.start_time <= start_time and end_time <= schedule.end_time

    @staticmethod
    def has_overlapping_booking(
            db: Session,
            professional: Professional,
            start: datetime.datetime,
            end: datetime.datetime
    ) -> bool:

        # Booking overlaps if: existing.start < new.end AND existing.end > new.start
        return db.query(Booking).filter(
            Booking.professional_id == professional.id,
            Booking.start < end,
            Booking.end > start
        ).count() > 0