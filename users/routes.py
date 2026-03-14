from .services import ClientService, ProfessionalService
from .utils import generate_auth_tokens, verify_password
from database import get_session
from users.models import Client
from users.schemas import (
    ClientAuthResponse,
    ClientSchema,
    ProfessionalAuthResponse,
    ProfessionalSchema,
    LoginSchema,
)

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


auth_router = APIRouter()
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
    tags=['User Management'],
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
    tags=['User Management'],
    status_code=status.HTTP_201_CREATED
)
def create_professional(schema: ProfessionalSchema = Depends(validate_professional), db: Session = Depends(get_session)):
    """Create a new professional."""
    try:
        professional = ProfessionalService.create(schema, db)
        ProfessionalService.initialize_schedule(db, professional)
        db.commit()

        tokens = generate_auth_tokens(professional.id)

        return {
            'user': professional,
            'tokens': tokens,
        }

    except IntegrityError:
        raise HTTPException(status_code=409, detail='Email already exists')


@auth_router.post('/login/', tags=['User Management'], status_code=status.HTTP_200_OK)
def login_user(schema: LoginSchema, db: Session = Depends(get_session)):
    user = ClientService.get_by_email(db, email=schema.email)
    if user is None:
        user = ProfessionalService.get_by_email(db, email=schema.email)

    if user is None or not verify_password(user.password, schema.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid email or password')

    tokens = generate_auth_tokens(user.id)
    if isinstance(user, Client):
        return ClientAuthResponse(user=user, tokens=tokens)

    return ProfessionalAuthResponse(user=user, tokens=tokens)
