from schedules.models import Schedule
from services.crud import ServiceCore
from users.services import ProfessionalService

import datetime
from typing import Optional, Self
from uuid import UUID

from pydantic import BaseModel, ValidationInfo, model_validator


WEEKDAYS = {
    1: Schedule.DayOfWeek.MONDAY,
    2: Schedule.DayOfWeek.TUESDAY,
    3: Schedule.DayOfWeek.WEDNESDAY,
    4: Schedule.DayOfWeek.THURSDAY,
    5: Schedule.DayOfWeek.FRIDAY,
    6: Schedule.DayOfWeek.SATURDAY,
    7: Schedule.DayOfWeek.SUNDAY,
}


class BookingSchema(BaseModel):
    service_id: UUID
    start: datetime.datetime
    professional_id: Optional[UUID] = None
    end: Optional[datetime.datetime] = None

    @model_validator(mode='after')
    def validate_availability_and_inject_relevant_data(self, info: ValidationInfo) -> Self:
        from .services import BookingService

        db = info.context.get('db_session')
        day_of_week = WEEKDAYS.get(self.start.isoweekday())
        service = ServiceCore.get_by_id(db, self.service_id)

        if service is None:
            raise ValueError('Service not found')

        professional = service.professional
        schedule = ProfessionalService.get_schedule(db, professional, day_of_week)

        if schedule is None:
            raise ValueError('Professional is not available on this day')

        end = self.start + datetime.timedelta(minutes=service.duration)
        if not BookingService.slot_fits_schedule(schedule, start=self.start, end=end):
            raise ValueError('Booking time outside professional schedule')

        if BookingService.has_overlapping_booking(db, professional, start=self.start, end=end):
            raise ValueError('Time slot already booked')

        self.professional_id = service.professional_id
        self.end = self.start + datetime.timedelta(minutes=service.duration)

        return self
