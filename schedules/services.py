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

    @staticmethod
    def create_schedule(
        professional: Professional,
        schedule_data: ScheduleSchema,
        db_session: Session | None = None
    ) -> Schedule:

        schedule = Schedule(
            professional=professional,
            day_of_week=schedule_data.day_of_week,
            start_time=schedule_data.start_time,
            end_time=schedule_data.end_time,
            is_available=schedule_data.is_available,
        )

        if db_session:
            db_session.add(schedule)

        return schedule
