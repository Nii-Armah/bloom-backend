from .models import Schedule

import datetime

from pydantic import BaseModel, ConfigDict, ValidationInfo, model_validator


class ScheduleOut(BaseModel):
    day_of_week: Schedule.DayOfWeek
    start_time: datetime.time
    end_time: datetime.time
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


class ScheduleSchema(BaseModel):
    day_of_week: Schedule.DayOfWeek
    start_time: datetime.time
    end_time: datetime.time
    is_available: bool = True

    @model_validator(mode='after')
    def validate_composite_uniqueness_of_professional_and_day_of_week_pair(self, info: ValidationInfo):
        db = (info.context or {}).get('db_session')
        professional = (info.context or {}).get('professional')

        if db and professional:
            exists = db.query(Schedule).filter(
                Schedule.professional == professional,
                Schedule.day_of_week == self.day_of_week
            ).first()

            if exists:
                raise ValueError('Professional already has a schedule for this day')

        return self
