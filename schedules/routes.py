from database import get_session
from dependencies import get_current_professional
from schedules.schemas import ScheduleOut
from schedules.services import ScheduleService
from users.models import Professional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status


schedules_router = APIRouter()


@schedules_router.get(
    '/',
    response_model=list[ScheduleOut],
    status_code=status.HTTP_200_OK,
    tags=['schedule Management']
)
async def get_schedules(
    professional: Professional = Depends(get_current_professional),
    db: Session = Depends(get_session)
):
    """Retrieves the schedule of a given professional."""
    schedules = ScheduleService.get_schedules_of_professional(db, professional)
    return schedules
