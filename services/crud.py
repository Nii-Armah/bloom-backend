from services.models import Service
from services.schemas import ServiceSchema
from users.models import Professional

from uuid import UUID

from sqlalchemy.orm import Session


class ServiceCore:
    @staticmethod
    def create(schema: ServiceSchema, db: Session, professional: Professional):
        data = schema.model_dump()
        data['professional_id'] = professional.id

        service = Service(**data)
        db.add(service)
        db.commit()
        db.refresh(service)

        return service

    @staticmethod
    def get_by_id(db: Session, service_id: UUID) -> Service | None:
        return db.query(Service).filter(Service.id == service_id).first()

    @staticmethod
    def get_services_of_professional(db: Session, professional: Professional) -> list[type[Service]]:
        return db.query(Service).filter(Service.professional == professional).all()