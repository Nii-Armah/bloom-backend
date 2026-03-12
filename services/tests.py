from .factories import ServiceFactory
from .models import Service
from .schemas import ServiceSchema
from database import init_db

import datetime
import decimal
from uuid import UUID

import factory
from pydantic import ValidationError
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
def service_data():
    return factory.build(dict, FACTORY_CLASS=ServiceFactory)


class TestServiceModel:
    def test_create_a_service(self, db_session, service_data) -> None:
        before = datetime.datetime.now()
        service = Service(**service_data)
        db_session.add(service)
        db_session.commit()

        assert isinstance(service.id, UUID)
        assert service.name == service_data.get('name')
        assert service.price == service_data.get('price')
        assert service.duration == service_data.get('duration')
        assert service.description == ''
        assert service.is_active
        assert service.professional == service_data.get('professional')
        assert before <= service.created_at <= datetime.datetime.now()
        assert before <= service.updated_at <= datetime.datetime.now()

    def test_required_service_fields(self, db_session, service_data):
        for field in service_data:
            data = factory.build(dict, FACTORY_CLASS=ServiceFactory)
            data.pop(field)
            service = Service(**data)
            db_session.add(service)

            with pytest.raises(IntegrityError) as exception:
                db_session.commit()

            db_session.rollback()
            exception_message = str(exception.value).split('\n')[0]
            assert exception_message.endswith(
                f'NOT NULL constraint failed: services.{'professional_id' if field == 'professional' else field}'
            )

    def test_service_name_is_unique_for_a_given_professional(self, db_session, service_data) -> None:
        service = Service(**service_data)
        db_session.add(service)
        db_session.commit()

        # Create a new service for same professional with same name
        service = Service(**service_data)
        db_session.add(service)

        with pytest.raises(IntegrityError) as exception:
            db_session.commit()

        exception_message = str(exception.value).split('\n')[0]
        assert exception_message.endswith('UNIQUE constraint failed: services.professional_id, services.name')


class TestServiceSchema:
    def test_valid_service_data(self, db_session, service_data) -> None:
        professional = service_data.pop('professional')
        schema = ServiceSchema.model_validate(
            service_data,
            context={'db_session': db_session, 'professional': professional}
        )
        validated_data = schema.model_dump()

        assert validated_data.get('name') == service_data.get('name')
        assert validated_data.get('description') == ''
        assert validated_data.get('price') == service_data.get('price')
        assert validated_data.get('duration') == service_data.get('duration')

    def test_required_service_fields(self, db_session, service_data) -> None:
        professional = service_data.pop('professional')

        for field in service_data:
            data = service_data.copy()
            data.pop(field)

            with pytest.raises(ValidationError) as exception:
                ServiceSchema.model_validate(data, context={'db_session': db_session, 'professional': professional})

            errors = exception.value.errors()
            assert len(errors) == 1
            assert errors[0].get('loc')[0] == field
            assert errors[0].get('msg') == 'Field required'

    def test_service_name_should_be_unique_for_a_given_professional(self, db_session, service_data) -> None:
        service = Service(**service_data)
        db_session.add(service)
        db_session.commit()

        professional = service_data.pop('professional')
        with pytest.raises(ValidationError) as exception:
            ServiceSchema.model_validate(service_data, context={'db_session': db_session, 'professional': professional})

        errors = exception.value.errors()
        assert len(errors) == 1
        assert errors[0].get('loc')[0] == 'name'
        assert errors[0].get('msg').endswith('Professional has a service by the given name')

    def test_service_duration_should_be_greater_than_zero(self, db_session, service_data) -> None:
        service_data.update({'duration': 0})
        professional = service_data.pop('professional')

        with pytest.raises(ValidationError) as exception:
            ServiceSchema.model_validate(service_data, context={'db_session': db_session, 'professional': professional})

        errors = exception.value.errors()
        assert len(errors) == 1
        assert errors[0].get('loc')[0] == 'duration'
        assert errors[0].get('msg') == 'Input should be greater than 0'

    def test_service_price_should_be_greater_than_zero(self, db_session, service_data) -> None:
        service_data.update({'price': decimal.Decimal('0.00')})
        professional = service_data.pop('professional')

        with pytest.raises(ValidationError) as exception:
            ServiceSchema.model_validate(service_data, context={'db_session': db_session, 'professional': professional})

        errors = exception.value.errors()
        assert len(errors) == 1
        assert errors[0].get('loc')[0] == 'price'
        assert errors[0].get('msg') == 'Input should be greater than 0'
