from .crud import ServiceCore
from .schemas import ServiceOut, ServiceSchema, ServiceDetailSchema
from database import get_session
from dependencies import get_current_professional
from services.models import Service
from users.models import Professional

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette import status


service_router = APIRouter()


async def validate_service(
        request: Request,
        db: Session = Depends(get_session),
        professional: Professional = Depends(get_current_professional)
):
    data = await request.json()
    return ServiceSchema.model_validate(data, context={'db_session': db, 'professional': professional})


@service_router.post(
    '/',
    response_model=ServiceOut,
    tags=['Service Management'],
    status_code=status.HTTP_201_CREATED
)
async def create_service(
        schema: ServiceSchema = Depends(validate_service),
        professional: Professional = Depends(get_current_professional),
        db: Session = Depends(get_session)
):
    """Create a new service."""
    try:
        service = ServiceCore.create(schema, db, professional)
        return service
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Service already exists')


@service_router.get(
    '/',
    response_model=list[ServiceOut],
    tags=['Service Management'],
    status_code=status.HTTP_200_OK
)
async def get_services(
        professional: Professional = Depends(get_current_professional),
        db: Session = Depends(get_session)
):
    """List all services of a given professional."""
    return ServiceCore.get_services_of_professional(db, professional)


@service_router.get(
    '/{service_id}/',
    response_model=ServiceDetailSchema,
    status_code=status.HTTP_200_OK,
    tags=['Service Management'],
)
def get_service_details(service_id: UUID, db: Session = Depends(get_session)):
    service = db.query(Service).filter(Service.id == service_id).first()

    if not service:
        raise HTTPException(status_code=404, detail='Service not found')

    return service