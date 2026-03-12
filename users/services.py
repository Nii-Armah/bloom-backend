from users.models import Client
from users.schemas import ClientSchema

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
