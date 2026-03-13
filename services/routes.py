from .crud import ServiceCore
from .schemas import ServiceOut, ServiceSchema
from database import get_session
from dependencies import get_current_professional
from users.models import Professional

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


@service_router.post('/',  response_model=ServiceOut, tags=['Service Management'], status_code=status.HTTP_201_CREATED)
async def create_service(
        schema: ServiceSchema = Depends(validate_service),
        professional: Professional = Depends(get_current_professional),
        db: Session = Depends(get_session)
):
    try:
        service = ServiceCore.create(schema, db, professional)
        return service
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Service already exists')
