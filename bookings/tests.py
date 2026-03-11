from .models import Booking
from .factories import BookingFactory
from database import init_db

import datetime
from uuid import UUID

import factory
import pytest
from sqlalchemy.exc import IntegrityError


@pytest.fixture(scope='function')
def db_session():
    engine, session_factory = init_db(test=True)
    session = session_factory()

    # Override FastAPI dependency
    # def override_get_session():
    #     return session

    # app.dependency_overrides[get_session] = override_get_session

    yield session

    session.close()
    engine.dispose()

@pytest.fixture(scope='function')
def booking_data():
    return factory.build(dict, FACTORY_CLASS=BookingFactory)


class TestBookingModel:
    def test_create_a_booking(self, booking_data, db_session) -> None:
        before = datetime.datetime.now()
        booking = Booking(**booking_data)
        db_session.add(booking)
        db_session.commit()

        assert isinstance(booking.id, UUID)
        assert booking.client == booking_data.get('client')
        assert booking.professional == booking_data.get('professional')
        assert booking.service == booking_data.get('service')
        assert booking.date == booking_data.get('date')
        assert booking.start_time == booking_data.get('start_time')
        assert booking.end_time == booking_data.get('end_time')
        assert booking.status == Booking.Status.CONFIRMED
        assert before <= booking.created_at <= datetime.datetime.now()
        assert before <= booking.updated_at <= datetime.datetime.now()

    def test_required_booking_fields(self, booking_data, db_session) -> None:
        for field in booking_data:
            data = booking_data.copy()
            data.pop(field)
            booking = Booking(**data)
            db_session.add(booking)

            with pytest.raises(IntegrityError) as exception:
                db_session.commit()
            db_session.rollback()

            exception_message = str(exception.value).split('\n')[0]
            if field in ['client', 'professional', 'service']:
                field = f'{field}_id'

            assert exception_message.endswith(f'NOT NULL constraint failed: bookings.{field}')

    def test_start_time_of_booking_should_precede_end_time(self, booking_data, db_session) -> None:
        data = booking_data.copy()
        data['end_time'] = datetime.time(7, 0, 0)
        assert data.get('end_time') < data.get('start_time')

        booking = Booking(**data)
        db_session.add(booking)

        with pytest.raises(IntegrityError) as exception:
            db_session.commit()

        exception_message = str(exception.value).split('\n')[0]
        assert exception_message.endswith('CHECK constraint failed: start_time_should_precede_end_time')
