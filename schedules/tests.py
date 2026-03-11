from .factories import ScheduleFactory
from .models import Schedule
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
