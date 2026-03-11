from .models import Schedule
from users.factories import ProfessionalFactory

import datetime
import random

import factory


class ScheduleFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Schedule

    professional = factory.SubFactory(ProfessionalFactory)
    day_of_week = factory.LazyFunction(lambda: random.choice([day for day in Schedule.DayOfWeek]))
    start_time = factory.LazyFunction(lambda: datetime.time(9, 0, 0))
    end_time = factory.LazyFunction(lambda: datetime.time(17, 0, 0))
