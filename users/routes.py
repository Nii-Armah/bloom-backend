from .services import ClientService, ProfessionalService
from .utils import generate_auth_tokens
from database import get_session
from users.schemas import ClientAuthResponse, ProfessionalAuthResponse, ClientSchema, ProfessionalSchema

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


client_router = APIRouter(prefix='/clients')
professional_router = APIRouter(prefix='/professionals')


async def validate_client(request: Request, db: Session = Depends(get_session)):
    data = await request.json()
    return ClientSchema.model_validate(data, context={'db_session': db})


async def validate_professional(request: Request, db: Session = Depends(get_session)):
    data = await request.json()
    return ProfessionalSchema.model_validate(data, context={'db_session': db})


@client_router.post(
    '/',
    response_model=ClientAuthResponse,
    tags=['Client Management'],
    status_code=status.HTTP_201_CREATED
)
async def create_client(schema: ClientSchema = Depends(validate_client),  db: Session = Depends(get_session)):
    """Create a new client."""
    try:
        client = ClientService.create(schema, db)
        tokens = generate_auth_tokens(client.id)
        return {
            'user': client,
            'tokens': tokens,
        }

    except IntegrityError:
        raise HTTPException(status_code=409, detail='Email already exists')


@professional_router.post(
    '/',
    response_model=ProfessionalAuthResponse,
    tags=['Professional Management'],
    status_code=status.HTTP_201_CREATED
)
def create_professional(schema: ProfessionalSchema = Depends(validate_professional), db: Session = Depends(get_session)):
    """Create a new professional."""
    try:
        professional = ProfessionalService.create(schema, db)
        tokens = generate_auth_tokens(professional.id)

        return {
            'user': professional,
            'tokens': tokens,
        }

    except IntegrityError:
        raise HTTPException(status_code=409, detail='Email already exists')
