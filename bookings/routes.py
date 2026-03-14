from bookings.services import BookingService
from bookings.schemas import BookingOutSchema, BookingSchema
from database import get_session
from dependencies import get_current_user, get_current_client
from users.models import Client, Professional
from users.services import ClientService, ProfessionalService

from typing import Union

from fastapi import APIRouter, Depends, Request
from fastapi_pagination import Page, paginate
from sqlalchemy.orm import Session
from starlette import status


bookings_router = APIRouter()


async def validate_booking(request: Request, db: Session = Depends(get_session)):
    data = await request.json()
    return BookingSchema.model_validate(data, context={'db_session': db})


@bookings_router.get('/', tags=['Booking Management'], response_model=Page[BookingOutSchema])
async def get_bookings(
        user: Union[Client, Professional] = Depends(get_current_user),
        db: Session = Depends(get_session)
):
    """Retrieves all bookings of a client or a professional."""
    service = ClientService if isinstance(user, Client) else ProfessionalService
    bookings = service.get_bookings(db, user)
    return paginate(bookings)


@bookings_router.post(
    '/',
    tags=['Booking Management'],
    response_model=BookingOutSchema,
    status_code=status.HTTP_201_CREATED
)
async def create_booking(
        client: Client = Depends(get_current_client),
        schema: BookingSchema = Depends(validate_booking),
        db: Session = Depends(get_session)
):
    """Creates a new booking for a given client."""
    return BookingService.create(db, schema, client)
