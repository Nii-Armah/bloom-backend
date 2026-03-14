from .models import Schedule

import datetime

from pydantic import BaseModel, ConfigDict


class ScheduleOut(BaseModel):
    day_of_week: Schedule.DayOfWeek
    start_time: datetime.time
    end_time: datetime.time
    is_available: bool

    model_config = ConfigDict(from_attributes=True)
