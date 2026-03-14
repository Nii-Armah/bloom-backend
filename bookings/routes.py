from bookings.schemas import BookingOutSchema
from database import get_session
from dependencies import get_current_user
from users.models import Client, Professional
from users.services import ClientService, ProfessionalService

from typing import Union

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, paginate
from sqlalchemy.orm import Session


bookings_router = APIRouter()


@bookings_router.get('/', tags=['Booking Management'], response_model=Page[BookingOutSchema])
async def get_bookings(
        user: Union[Client, Professional] = Depends(get_current_user),
        db: Session = Depends(get_session)
):
    """Retrieves all bookings of a client or a professional."""
    service = ClientService if isinstance(user, Client) else ProfessionalService
    bookings = service.get_bookings(db, user)
    return paginate(bookings)
