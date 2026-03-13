from users.models import Client, Professional
from users.schemas import ClientSchema, ProfessionalSchema
from schedules.models import Schedule

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
