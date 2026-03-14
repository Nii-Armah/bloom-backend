from users.models import Client, Professional
from users.utils import generate_auth_tokens
from .factories import BookingFactory
from .models import Booking
from .schemas import BookingSchema
from app import create_app
from database import Base, get_session, init_db
from schedules.factories import ScheduleFactory
from schedules.models import Schedule
from users.services import ProfessionalService

from users.factories import ClientFactory, ProfessionalFactory
from services.crud import ServiceCore
from services.factories import ServiceFactory

import datetime
from uuid import UUID

import factory
from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest
from sqlalchemy.exc import IntegrityError
from starlette import status


@pytest.fixture(scope='function')
def app():
    return create_app()


@pytest.fixture(scope='function')
def db_session(app):
    engine, session_factory = init_db(test=True)
    Base.metadata.create_all(bind=engine)

    connection = engine.connect()
    transaction = connection.begin()
    session = session_factory(bind=connection)

    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    yield session

    session.close()
    transaction.rollback()
    connection.close()
    engine.dispose()


@pytest.fixture(scope='function')
def client(app, db_session):
    return TestClient(app)


@pytest.fixture(scope='function')
def booking_data():
    return factory.build(dict, FACTORY_CLASS=BookingFactory)


@pytest.fixture(scope='function')
def booking_schema_data(db_session):
    ProfessionalFactory._meta.sqlalchemy_session = db_session
    ServiceFactory._meta.sqlalchemy_session = db_session

    service = ServiceFactory.create(duration=60)
    db_session.flush()

    return {
        'service_id': service.id,
        'start': datetime.datetime(2026, 3, 13, 10, 0, 0),
    }


@pytest.fixture(scope='function')
def weekday():
    return {
        1: Schedule.DayOfWeek.MONDAY,
        2: Schedule.DayOfWeek.TUESDAY,
        3: Schedule.DayOfWeek.WEDNESDAY,
        4: Schedule.DayOfWeek.THURSDAY,
        5: Schedule.DayOfWeek.FRIDAY,
        6: Schedule.DayOfWeek.SATURDAY,
        7: Schedule.DayOfWeek.SUNDAY,
    }


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
        assert booking.start == booking_data.get('start')
        assert booking.end == booking_data.get('end')
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
        data['end'] = data.get('start') - datetime.timedelta(minutes=60)
        assert data.get('end') < data.get('start')

        booking = Booking(**data)
        db_session.add(booking)

        with pytest.raises(IntegrityError) as exception:
            db_session.commit()

        exception_message = str(exception.value).split('\n')[0]
        assert exception_message.endswith('CHECK constraint failed: start_should_precede_end')


class TestBookingSchema:
    @staticmethod
    def get_professional_and_day_of_week(db_session, schema_data, weekday):
        service_id = schema_data.get('service_id')
        service = ServiceCore.get_by_id(db_session, service_id)
        professional = service.professional
        day_of_week = weekday.get(schema_data.get('start').isoweekday())

        return professional, day_of_week

    @classmethod
    def create_schedule_for_professional(cls, db_session, schema_data, weekday):
        ScheduleFactory._meta.sqlalchemy_session = db_session
        professional, day_of_week = cls.get_professional_and_day_of_week(db_session, schema_data, weekday)
        schedule = ScheduleFactory.create(professional=professional, day_of_week=day_of_week)
        db_session.flush()

        return schedule

    def test_valid_booking_data(self, booking_schema_data, db_session, weekday) -> None:
        self.create_schedule_for_professional(db_session, booking_schema_data, weekday)
        validated_booking = BookingSchema.model_validate(booking_schema_data, context={'db_session': db_session})

        assert validated_booking.service_id == booking_schema_data.get('service_id')
        service = ServiceCore.get_by_id(db_session, validated_booking.service_id)
        assert validated_booking.professional_id == service.professional.id
        assert validated_booking.start == booking_schema_data.get('start')
        assert validated_booking.end == booking_schema_data.get('start') + datetime.timedelta(minutes=service.duration)

    def test_required_booking_fields(self, booking_schema_data, db_session) -> None:
        for field in booking_schema_data:
            data = booking_schema_data.copy()
            data.pop(field)
            with pytest.raises(ValidationError) as exception:
                BookingSchema.model_validate(data, context={'db_session': db_session})

            error = exception.value.errors()[0]
            assert error['type'] == 'missing'
            assert error['msg'] == 'Field required'
            assert error['loc'][0] == field

    def test_professional_should_have_schedule_on_booking_day(self, db_session, weekday, booking_schema_data) -> None:
        professional, booking_day = self.get_professional_and_day_of_week(db_session, booking_schema_data, weekday)

        # Professional is not available on the booking day
        assert ProfessionalService.get_schedule(db_session, professional, booking_day) is None

        with pytest.raises(ValidationError) as exception:
            BookingSchema.model_validate(booking_schema_data, context={'db_session': db_session})

        error = exception.value.errors()[0]
        assert error['type'] == 'value_error'
        assert error['msg'].endswith('Professional is not available on this day')

    def test_booking_time_should_fit_within_professional_schedule(self, booking_schema_data, db_session, weekday) -> None:
        schedule = self.create_schedule_for_professional(db_session, booking_schema_data, weekday)

        # start time is before schedule start time
        booking_data = booking_schema_data.copy()
        booking_data.update({'start': datetime.datetime.combine(
            booking_schema_data.get('start').date(), datetime.time(4, 0, 0)
        )})
        assert booking_data.get('start').time() < schedule.start_time

        with pytest.raises(ValidationError) as exception:
            BookingSchema.model_validate(booking_data, context={'db_session': db_session})

        error = exception.value.errors()[0]
        assert error['type'] == 'value_error'
        assert error['msg'].endswith('Booking time outside professional schedule')

    def test_booking_slot_should_have_no_overlap(self, booking_schema_data, db_session, weekday) -> None:
        self.create_schedule_for_professional(db_session, booking_schema_data, weekday)

        service = ServiceCore.get_by_id(db_session, booking_schema_data.get('service_id'))
        professional = service.professional
        BookingFactory._meta.sqlalchemy_session = db_session
        ClientFactory._meta.sqlalchemy_session = db_session
        client = ClientFactory.create()

        existing_booking = Booking(
            client_id=client.id,
            service_id=booking_schema_data.get('service_id'),
            start=booking_schema_data.get('start') + datetime.timedelta(minutes=20),
            end=booking_schema_data.get('start') + datetime.timedelta(minutes=60),
            professional_id=professional.id
        )
        db_session.add(existing_booking)
        db_session.flush()

        assert db_session.query(Booking).filter(Booking.professional== professional).count() == 1

        with pytest.raises(ValidationError) as exception:
            BookingSchema.model_validate(booking_schema_data, context={'db_session': db_session})

        error = exception.value.errors()[0]
        assert error['type'] == 'value_error'
        assert error['msg'].endswith('Time slot already booked')


class TestBookingManagementEndpoints:
    def test_booking_listing_endpoint_is_authenticated(self, client, assert_auth_error) -> None:
        response = client.get('/api/v1/bookings/')
        assert_auth_error(response, status.HTTP_401_UNAUTHORIZED, 'Not authenticated')

    def test_get_all_bookings_of_a_professional(self, client, db_session) -> None:
        professional_data = factory.build(dict, FACTORY_CLASS=ProfessionalFactory)
        professional = Professional(**professional_data)
        db_session.add(professional)
        db_session.flush()

        tokens = generate_auth_tokens(professional.id)
        header = {'Authorization': f'Bearer {tokens.get("access_token")}'}

        # No booking
        assert db_session.query(Booking).filter(Booking.professional == professional).count() == 0
        response = client.get('/api/v1/bookings/', headers=header)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json().get('items')) == 0

        # Create a booking
        booking_data = factory.build(dict, FACTORY_CLASS=BookingFactory)
        booking_data.update({'professional': professional})
        booking = Booking(**booking_data)
        db_session.add(booking)
        db_session.flush()

        response = client.get('/api/v1/bookings/', headers=header)
        assert response.status_code == status.HTTP_200_OK
        items = response.json().get('items')
        assert len(items) == 1

        booking_data = items[0]
        assert booking_data.get('id') == str(booking.id)
        assert booking_data.get('service')
        assert booking_data.get('start')
        assert booking_data.get('end')
        assert booking_data.get('status') == booking.status.value


    def test_get_all_bookings_of_a_client(self, client, db_session) -> None:
        client_data = factory.build(dict, FACTORY_CLASS=ClientFactory)
        client_instance = Client(**client_data)
        db_session.add(client_instance)
        db_session.flush()

        tokens = generate_auth_tokens(client_instance.id)
        header = {'Authorization': f'Bearer {tokens.get("access_token")}'}

        # No booking
        response = client.get('/api/v1/bookings/', headers=header)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json().get('items')) == 0

        # Create a booking
        booking_data = factory.build(dict, FACTORY_CLASS=BookingFactory)
        booking_data.update({'client': client_instance})
        booking = Booking(**booking_data)
        db_session.add(booking)
        db_session.flush()

        response = client.get('/api/v1/bookings/', headers=header)
        assert response.status_code == status.HTTP_200_OK
        items = response.json().get('items')
        assert len(items) == 1

        booking_data = items[0]
        assert booking_data.get('id') == str(booking.id)
        assert booking_data.get('service')
        assert booking_data.get('start')
        assert booking_data.get('end')
        assert booking_data.get('status') == booking.status.value
