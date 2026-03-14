from schedules.models import Schedule
from schedules.schemas import ScheduleSchema
from users.models import Professional

from sqlalchemy.orm import Session


class ScheduleService:
    @staticmethod
    def get_schedules_of_professional(db: Session, professional: Professional):
        return db.query(Schedule).filter(Schedule.professional == professional).all()

    @staticmethod
    def get_schedule_by_professional_and_day_of_week(
        db: Session,
        professional: Professional,
        day_of_week: Schedule.DayOfWeek
    ) -> Schedule | None:

        return db.query(Schedule).filter(
            Schedule.professional == professional,
            Schedule.day_of_week == day_of_week
        ).first()

    @staticmethod
    def update_schedule(db_schedule: Schedule, schema: ScheduleSchema):
        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_schedule, key, value)

        return db_schedule
