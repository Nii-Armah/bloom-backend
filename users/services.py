from bookings.models import Booking
from schedules.models import Schedule
from schedules.schemas import ScheduleSchema
from schedules.services import ScheduleService
from users.models import Client, Professional
from users.schemas import ClientSchema, ProfessionalSchema

import datetime
from uuid import UUID

from sqlalchemy.orm import Session


class ClientService:
    @staticmethod
    def create(schema: ClientSchema, db: Session) -> Client:
        data = schema.model_dump()
        client = Client(**data)
        db.add(client)
        db.commit()
        db.refresh(client)

        return client

    @staticmethod
    def get_by_id(db: Session, client_id: UUID) -> Client | None:
        return db.query(Client).filter(Client.id == client_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Client | None:
        return db.query(Client).filter(Client.email == email).first()

    @staticmethod
    def get_bookings(db: Session, client: Client) -> list[type[Booking]]:
        return db.query(Booking).filter(Booking.client == client).all()


class ProfessionalService:
    @staticmethod
    def create(schema: ProfessionalSchema, db: Session) -> Professional:
        data = schema.model_dump()
        professional = Professional(**data)
        db.add(professional)
        db.commit()
        db.refresh(professional)

        return professional

    @staticmethod
    def get_by_id(db: Session, client_id: UUID) -> Professional | None:
        return db.query(Professional).filter(Professional.id == client_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Professional | None:
        return db.query(Professional).filter(Professional.email == email).first()

    @staticmethod
    def get_schedule(db: Session, professional: Professional, day: Schedule.DayOfWeek) -> Schedule | None:
        return db.query(Schedule).filter(
            Schedule.professional == professional,
            Schedule.day_of_week == day
        ).first()

    @staticmethod
    def initialize_schedule(db: Session, professional: Professional) -> None:
        weekends = [Schedule.DayOfWeek.SATURDAY, Schedule.DayOfWeek.SUNDAY]

        for day_of_week in Schedule.DayOfWeek:
            schedule_data = ScheduleSchema(
                day_of_week=day_of_week,
                start_time=datetime.time(9, 0, 0),
                end_time=datetime.time(17, 0, 0),
                is_available=False if day_of_week in weekends else True
            )
            ScheduleService.create_schedule(professional, schedule_data, db)

    @staticmethod
    def get_bookings(db: Session, professional: Professional) -> list[type[Booking]]:
        return db.query(Booking).filter(Booking.professional == professional).all()
