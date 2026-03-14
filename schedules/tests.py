from .factories import ScheduleFactory
from .models import Schedule
from app import create_app
from database import Base, get_session, init_db
from users.factories import ProfessionalFactory
from users.utils import generate_auth_tokens

import datetime
from uuid import UUID

import factory
from fastapi.testclient import TestClient
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
def schedule_data():
    return factory.build(dict, FACTORY_CLASS=ScheduleFactory)


class TestScheduleModel:
    def test_create_a_schedule(self, db_session, schedule_data) -> None:
        before = datetime.datetime.now()
        schedule = Schedule(**schedule_data)
        db_session.add(schedule)
        db_session.commit()

        assert isinstance(schedule.id, UUID)
        assert schedule.professional == schedule_data.get('professional')
        assert schedule.day_of_week == schedule_data.get('day_of_week')
        assert schedule.start_time == schedule_data.get('start_time')
        assert schedule.end_time == schedule_data.get('end_time')
        assert schedule.is_available
        assert before <= schedule.created_at <= datetime.datetime.now()
        assert before <= schedule.updated_at <= datetime.datetime.now()

    def test_required_schedule_fields(self, db_session, schedule_data) -> None:
        for field in schedule_data:
            data = schedule_data.copy()
            data.pop(field)
            schedule = Schedule(**data)
            db_session.add(schedule)

            with pytest.raises(IntegrityError) as exception:
                db_session.commit()
            db_session.rollback()

            exception_message = str(exception.value).split('\n')[0]
            assert exception_message.endswith(
                f'NOT NULL constraint failed: schedules.{'professional_id' if field == 'professional' else field}'
            )

    def test_start_time_of_schedule_cannot_precede_end_time(self, db_session, schedule_data) -> None:
        data = schedule_data.copy()
        data['end_time'] = datetime.time(6, 0, 0)
        assert data.get('end_time') < data.get('start_time')

        schedule = Schedule(**data)
        db_session.add(schedule)
        with pytest.raises(IntegrityError) as exception:
            db_session.commit()

        exception_message = str(exception.value).split('\n')[0]
        assert exception_message.endswith('CHECK constraint failed: check_start_before_end')


    def test_day_of_week_is_unique_for_a_given_professional(self, db_session, schedule_data) -> None:
        schedule = Schedule(**schedule_data)
        db_session.add(schedule)
        db_session.commit()

        # Attempt to create a same day schedule for same professional
        schedule = Schedule(**schedule_data)
        db_session.add(schedule)
        with pytest.raises(IntegrityError) as exception:
            db_session.commit()

        exception_message = str(exception.value).split('\n')[0]
        assert exception_message.endswith('UNIQUE constraint failed: schedules.professional_id, schedules.day_of_week')


class TestScheduleManagementEndpoints:
    def test_retrieve_all_schedules_of_a_professional(self, client, db_session) -> None:
        ProfessionalFactory._meta.sqlalchemy_session = db_session
        ScheduleFactory._meta.sqlalchemy_session = db_session
        professional = ProfessionalFactory.create()
        for day in Schedule.DayOfWeek:
            ScheduleFactory.create(professional=professional, day_of_week=day)

        db_session.flush()

        assert db_session.query(Schedule).filter(Schedule.professional == professional).count() == 7

        tokens = generate_auth_tokens(professional.id)
        header = {'Authorization': f'Bearer {tokens.get('access_token')}'}
        response = client.get('/api/v1/schedules/', headers=header)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 7

    def test_schedule_listing_endpoint_is_authenticated(self, client, assert_auth_error) -> None:
        response = client.get('/api/v1/schedules/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert_auth_error(response, status.HTTP_401_UNAUTHORIZED, 'Not authenticated')
