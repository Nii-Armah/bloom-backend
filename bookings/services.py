from .models import Booking
from bookings.schemas import BookingSchema
from schedules.models import Schedule
from users.models import Client, Professional

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

    @staticmethod
    def create(db: Session, schema: BookingSchema, client: Client) -> Booking:
        booking = Booking(**schema.model_dump())
        booking.client_id = client.id
        db.add(booking)
        db.commit()
        db.refresh(booking)

        return booking
