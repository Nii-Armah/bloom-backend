from users.models import Client, Professional
from users.schemas import ClientSchema, ProfessionalSchema

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
