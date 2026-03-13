from .factories import ServiceFactory
from .models import Service
from .schemas import ServiceSchema
from app import create_app
from database import Base, get_session, init_db
from users.factories import ClientFactory, ProfessionalFactory
from users.utils import generate_auth_tokens

import datetime
import decimal
import os
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
def service_data():
    return factory.build(dict, FACTORY_CLASS=ServiceFactory)


@pytest.fixture(scope='function')
def professional_auth_header(db_session):
    ProfessionalFactory._meta.sqlalchemy_session = db_session
    professional = ProfessionalFactory.create()
    tokens = generate_auth_tokens(professional.id)

    return {
        'professional': professional,
        'header': {'Authorization': f'Bearer {tokens.get('access_token')}'}
    }


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


class TestServiceManagementAPIEndpoints:
    def test_service_creation_endpoint_is_authenticated(self, client, service_data, assert_auth_error) -> None:
        service_data.pop('professional')
        service_data.update({'price': str(service_data.get('price'))})

        response = client.post('/api/v1/services/', json=service_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert_auth_error(response, status_code=status.HTTP_401_UNAUTHORIZED, message='Not authenticated')

    def test_endpoint_is_only_accessible_by_professionals(
            self, client, db_session, service_data, assert_auth_error
    ) -> None:
        ClientFactory._meta.sqlalchemy_session = db_session
        user = ClientFactory.create()
        db_session.add(user)
        db_session.commit()

        tokens = generate_auth_tokens(user.id)
        header = {'Authorization': f'Bearer {tokens.get('access_token')}'}
        service_data.pop('professional')
        service_data.update({'price': str(service_data.get('price'))})
        response = client.post('/api/v1/services/', json=service_data, headers=header)
        assert_auth_error(
            response,
            status_code=status.HTTP_403_FORBIDDEN,
            message='Access denied. Professional account required.'
        )

    def test_create_a_service(self, client, db_session, professional_auth_header, service_data) -> None:
        service_data.pop('professional')
        service_data.update({'price': str(service_data.get('price'))})

        professional = professional_auth_header.get('professional')
        assert db_session.query(Service).where(Service.professional == professional).count() == 0

        auth_header = professional_auth_header.get('header')
        response = client.post('/api/v1/services/', json=service_data, headers=auth_header)
        assert response.status_code == status.HTTP_201_CREATED

        response_data = response.json()
        assert response_data.get('name') == service_data.get('name')
        assert response_data.get('description') == ''
        assert response_data.get('price') == str(service_data.get('price'))
        assert response_data.get('duration') == service_data.get('duration')
        assert response_data.get('is_active')

        assert db_session.query(Service).where(Service.professional == professional).count() == 1

    def test_required_service_fields(self, client, service_data, professional_auth_header, assert_validation_error) -> None:
        service_data.pop('professional')
        service_data.update({'price': str(service_data.get('price'))})

        auth_header = professional_auth_header.get('header')
        for field in service_data:
            data = service_data.copy()
            data.pop(field)

            response = client.post('/api/v1/services/', json=data, headers=auth_header)
            assert_validation_error(response, field_name=field)

    def test_price_of_service_should_be_positive(
            self, client, service_data, professional_auth_header, assert_validation_error
    ) -> None:
        service_data.pop('professional')
        service_data.update({'price': '-5.00'}) # -5 cedis

        auth_header = professional_auth_header.get('header')

        response = client.post('/api/v1/services/', json=service_data, headers=auth_header)
        assert_validation_error(response, field_name='price')

        service_data.update({'price': '0.00'})  # 0 cedis
        response = client.post('/api/v1/services/', json=service_data, headers=auth_header)
        assert_validation_error(response, field_name='price')

    def test_duration_of_service_should_be_positive(
            self, client, professional_auth_header, service_data, assert_validation_error
    ) -> None:
        service_data.pop('professional')
        service_data.update({
            'duration': -30,  # -30 minutes
            'price': str(service_data.get('price'))
        })

        auth_header = professional_auth_header.get('header')

        response = client.post('/api/v1/services/', json=service_data, headers=auth_header)
        assert_validation_error(response, field_name='duration')

        service_data.update({'duration': 0})  # 0 minutes
        response = client.post('/api/v1/services/', json=service_data, headers=auth_header)
        assert_validation_error(response, field_name='duration')

    def test_service_name_should_be_unique_per_professional(
            self, client, db_session, service_data, professional_auth_header, assert_validation_error
    ) -> None:
        professional = professional_auth_header.get('professional')
        service_data.update({'professional': professional})
        service = Service(**service_data)
        db_session.add(service)
        db_session.commit()

        assert db_session.query(Service).where(Service.professional == professional).count() == 1
        assert service.name == service_data.get('name')

        service_data.pop('professional')
        service_data.update({'price': str(service_data.get('price'))})
        auth_header = professional_auth_header.get('header')
        response = client.post('/api/v1/services/', json=service_data, headers=auth_header)
        assert_validation_error(response, field_name='name')

    @pytest.mark.skipif('sqlite' in os.getenv('DATABASE_URL'), reason='SQLite has limited concurrency')
    def test_service_creation_race_condition(self, db_session, service_data) -> None:
        from threading import Thread

        professional = service_data['professional']
        results = {'errors': 0, 'success': 0}

        def create_service():
            try:
                service = Service(**service_data)
                db_session.add(service)
                db_session.commit()
                results['success'] += 1
            except IntegrityError:
                db_session.rollback()
                results['errors'] += 1

        t1 = Thread(target=create_service)
        t2 = Thread(target=create_service)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert results['success'] == 1
        assert results['errors'] == 1

        assert db_session.query(Service).where(
            Service.professional_id == professional.id,
            Service.name == service_data.get('name')
        ).count() == 1

    def test_retrieve_all_services_of_professional(self, client, service_data, db_session, professional_auth_header) -> None:
        professional = professional_auth_header.get('professional')
        service_data.update({'professional': professional})
        service = Service(**service_data)
        db_session.add(service)
        db_session.commit()

        assert db_session.query(Service).filter(Service.professional == professional).count() == 1

        headers = professional_auth_header.get('header')
        response = client.get('/api/v1/services/', headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 1

        created_service_data = response.json()[0]
        assert created_service_data.get('name') == service_data.get('name')
        assert created_service_data.get('description') == ''
        assert created_service_data.get('price') == str(service_data.get('price'))
        assert created_service_data.get('duration') == service_data.get('duration')

    def test_services_retrieval_endpoint_is_authenticated(self, client, assert_auth_error) -> None:
        response = client.get('/api/v1/services/')
        assert_auth_error(response, status_code=401, message='Not authenticated')
