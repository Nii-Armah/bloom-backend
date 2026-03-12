from .services import ClientService
from .utils import generate_auth_tokens
from database import get_session
from users.schemas import ClientSchema, AuthResponse

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


router = APIRouter(prefix='/clients')


async def validate_client(request: Request, db: Session = Depends(get_session)):
    data = await request.json()
    return ClientSchema.model_validate(data, context={'db_session': db})


@router.post('/', response_model=AuthResponse)
async def create_client(schema: ClientSchema = Depends(validate_client),  db: Session = Depends(get_session)):
    try:
        client = ClientService.create(schema, db)
        tokens = generate_auth_tokens(client.id)
        return {
            'user': client,
            'tokens': tokens,
        }

    except IntegrityError:
        raise HTTPException(status_code=409, detail='Email already exists')
