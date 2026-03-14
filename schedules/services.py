from schedules.models import Schedule
from users.models import Professional

from sqlalchemy.orm import Session


class ScheduleService:
    @staticmethod
    def get_schedules_of_professional(db: Session, professional: Professional):
        return db.query(Schedule).filter(Schedule.professional == professional).all()
