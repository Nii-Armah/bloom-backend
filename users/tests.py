from .factories import ClientFactory, ProfessionalFactory
from .models import Client, Professional
from .schemas import ClientSchema, ProfessionalSchema
from .services import ClientService, ProfessionalService
from .utils import decode_token, verify_password
from app import create_app
from database import Base, get_session, init_db
from schedules.models import Schedule
from services.models import Service

import datetime
from uuid import UUID

import factory
from fastapi import status
from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest
from sqlalchemy import func, select, exists
from sqlalchemy.exc import IntegrityError


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
def client_data():
    return factory.build(dict, FACTORY_CLASS=ClientFactory)


@pytest.fixture(scope='function')
def professional_data():
    return factory.build(dict, FACTORY_CLASS=ProfessionalFactory)


@pytest.fixture(scope='function')
def client_login_data(client_data):
    return {
        'email': client_data.get('email'),
        'password': client_data.get('password')
    }


@pytest.fixture(scope='function')
def professional_login_data(professional_data):
    return {
        'email': professional_data.get('email'),
        'password': professional_data.get('password'),
    }


class TestClientModel:
    def test_create_a_client(self, client_data, db_session) -> None:
        before = datetime.datetime.now()
        client = Client(**client_data)
        db_session.add(client)
        db_session.commit()

        assert isinstance(client.id, UUID)
        assert client.full_name == client_data.get('full_name')
        assert client.email == client_data.get('email')
        assert client.contact_number == ''
        assert verify_password(client.password, client_data.get('password'))
        assert before <= client.created_at <= datetime.datetime.now()
        assert before <= client.created_at <= datetime.datetime.now()

    def test_required_client_fields(self, client_data, db_session) -> None:
        for field in client_data:
            data = client_data.copy()
            data.pop(field)
            client = Client(**data)
            db_session.add(client)

            with pytest.raises(IntegrityError) as exception:
                db_session.commit()
            db_session.rollback()

            exception_message = str(exception.value).split('\n')[0]
            assert exception_message.endswith(f'NOT NULL constraint failed: clients.{field}')

    def test_password_of_client_is_hashed(self, client_data, db_session) -> None:
        client = Client(**client_data)
        db_session.add(client)
        db_session.commit()

        assert client.password != client_data.get('password')

    def test_email_of_client_is_unique(self, client_data, db_session) -> None:
        client = Client(**client_data)
        db_session.add(client)
        db_session.commit()

        # Attempt to create another client with the same email address
        client = Client(**client_data)
        db_session.add(client)
        with pytest.raises(IntegrityError) as exception:
            db_session.commit()

        exception_message = str(exception.value).split('\n')[0]
        assert exception_message.endswith(f'UNIQUE constraint failed: clients.email')


class TestProfessionalModel:
    def test_create_a_professional(self, professional_data, db_session) -> None:
        before = datetime.datetime.now()
        professional = Professional(**professional_data)
        db_session.add(professional)
        db_session.commit()

        assert isinstance(professional.id, UUID)
        assert professional.full_name == professional_data.get('full_name')
        assert professional.email == professional_data.get('email')
        assert professional.bio == ''
        assert not professional.is_verified
        assert professional.specialty == professional_data.get('specialty')
        assert verify_password(professional.password, professional_data.get('password'))
        assert db_session.query(Service).filter_by(professional_id=professional.id).all() == []
        assert db_session.query(Schedule).filter_by(professional_id=professional.id).all() == []
        assert before <= professional.created_at <= datetime.datetime.now()
        assert before <= professional.updated_at <= datetime.datetime.now()

    def test_required_professional_fields(self, db_session, professional_data) -> None:
        for field in professional_data:
            data = professional_data.copy()
            data.pop(field)
            professional = Professional(**data)
            db_session.add(professional)

            with pytest.raises(IntegrityError) as exception:
                db_session.commit()
            db_session.rollback()

            exception_message = str(exception.value).split('\n')[0]
            assert exception_message.endswith(f'NOT NULL constraint failed: professionals.{field}')

    def test_password_of_professional_is_hashed(self, db_session, professional_data) -> None:
        professional = Professional(**professional_data)
        db_session.add(professional)
        db_session.commit()

        assert professional.password != professional_data.get('password')

    def test_email_of_professional_is_unique(self, db_session, professional_data) -> None:
        professional = Professional(**professional_data)
        db_session.add(professional)
        db_session.commit()

        # Attempt to create another professional with the same email address
        professional = Professional(**professional_data)
        db_session.add(professional)

        with pytest.raises(IntegrityError) as exception:
            db_session.commit()

        exception_message = str(exception.value).split('\n')[0]
        assert exception_message.endswith(f'UNIQUE constraint failed: professionals.email')


class TestClientSchema:
    def test_valid_client_data(self, client_data, db_session) -> None:
        client_data.update({'password2': client_data.get('password')})
        schema = ClientSchema.model_validate(client_data, context={'db_session': db_session})
        validated_data = schema.model_dump()

        assert validated_data.get('full_name') == client_data.get('full_name')
        assert validated_data.get('email') == client_data.get('email')
        assert validated_data.get('contact_number') == ''
        assert validated_data.get('password') == client_data.get('password')
        assert 'password2' not in validated_data

    def test_required_client_fields(self, client_data, db_session) -> None:
        client_data.update({'password2': 'Different1234$'})

        for field in client_data:
            data = client_data.copy()
            data.pop(field)

            with pytest.raises(ValidationError) as exception:
                ClientSchema.model_validate(data, context={'db_session': db_session})

            errors = exception.value.errors()
            assert len(errors) == 1
            assert errors[0].get('loc')[0] == field
            assert errors[0].get('msg') == 'Field required'

    def test_client_data_with_invalid_email(self, client_data, db_session) -> None:
        client_data.update({
            'password2': 'Different1234$',
            'email': 'invalid_email'
        })

        with pytest.raises(ValidationError) as exception:
            ClientSchema.model_validate(client_data, context={'db_session': db_session})

        errors = exception.value.errors()
        assert len(errors) == 1
        assert errors[0].get('loc')[0] == 'email'
        assert errors[0].get('msg').endswith('An email address must have an @-sign.')

    def test_client_data_with_invalid_password(self, client_data, db_session) -> None:
        client_data.update({'password': '1234', 'password2': '1234'})
        with pytest.raises(ValidationError) as exception:
            ClientSchema.model_validate(client_data, context={'db_session': db_session})

        errors = exception.value.errors()
        assert len(errors) == 1
        assert errors[0].get('loc')[0] == 'password'
        assert errors[0].get('msg').endswith('Password should have a minimum of 8 characters')

    def test_client_data_with_unmatching_passwords(self, client_data, db_session) -> None:
        client_data.update({'password2': 'Different1234$'})
        assert client_data.get('password') != client_data.get('password2')

        with pytest.raises(ValidationError) as exception:
            ClientSchema.model_validate(client_data, context={'db_session': db_session})

        errors = exception.value.errors()
        assert len(errors) == 1
        assert errors[0].get('msg').endswith('Passwords do not match')

    def test_client_data_with_existing_email(self, client_data, db_session) -> None:
        client = Client(**client_data)
        db_session.add(client)
        db_session.commit()

        client_data.update({'password2': client_data.get('password')})
        with pytest.raises(ValidationError) as exception:
            ClientSchema.model_validate(client_data, context={'db_session': db_session})

        errors = exception.value.errors()
        assert len(errors) == 1
        assert errors[0].get('loc')[0] == 'email'
        assert errors[0].get('msg').endswith('Email already exists')


class TestProfessionalSchema:
    def test_valid_professional_data(self, db_session, professional_data) -> None:
        professional_data.update({'password2': professional_data.get('password')})
        schema = ProfessionalSchema.model_validate(professional_data, context={'db_session': db_session})
        validated_data = schema.model_dump()

        assert validated_data.get('full_name') == professional_data.get('full_name')
        assert validated_data.get('email') == professional_data.get('email')
        assert validated_data.get('bio') == ''
        assert validated_data.get('password') == professional_data.get('password')
        assert 'password2' not in validated_data

    def test_required_professional_fields(self, db_session, professional_data) -> None:
        professional_data.update({'password2': 'Different1234$'})

        for field in professional_data:
            data = professional_data.copy()
            data.pop(field)

            with pytest.raises(ValidationError) as exception:
                ProfessionalSchema.model_validate(data, context={'db_session': db_session})

            errors = exception.value.errors()
            assert len(errors) == 1
            assert errors[0].get('loc')[0] == field
            assert errors[0].get('msg') == 'Field required'

    def test_professional_data_with_invalid_email(self,  db_session, professional_data) -> None:
        professional_data.update({
            'password2': 'Different1234$',
            'email': 'invalid_email'
        })

        with pytest.raises(ValidationError) as exception:
            ProfessionalSchema.model_validate(professional_data, context={'db_session': db_session})

        errors = exception.value.errors()
        assert len(errors) == 1
        assert errors[0].get('loc')[0] == 'email'
        assert errors[0].get('msg').endswith('An email address must have an @-sign.')

    def test_professional_data_with_invalid_password(self, db_session, professional_data) -> None:
        professional_data.update({'password': '1234', 'password2': '1234'})
        with pytest.raises(ValidationError) as exception:
            ProfessionalSchema.model_validate(professional_data, context={'db_session': db_session})

        errors = exception.value.errors()
        assert len(errors) == 1
        assert errors[0].get('loc')[0] == 'password'
        assert errors[0].get('msg').endswith('Password should have a minimum of 8 characters')

    def test_professional_data_with_unmatching_passwords(self, db_session, professional_data) -> None:
        professional_data.update({'password2': 'Different1234$'})
        assert professional_data.get('password') != professional_data.get('password2')

        with pytest.raises(ValidationError) as exception:
            ProfessionalSchema.model_validate(professional_data, context={'db_session': db_session})

        errors = exception.value.errors()
        assert len(errors) == 1
        assert errors[0].get('msg').endswith('Passwords do not match')

    def test_professional_data_with_existing_email(self, db_session, professional_data) -> None:
        professional = Professional(**professional_data)
        db_session.add(professional)
        db_session.commit()

        professional_data.update({'password2': professional_data.get('password')})
        with pytest.raises(ValidationError) as exception:
            ProfessionalSchema.model_validate(professional_data, context={'db_session': db_session})

        errors = exception.value.errors()
        assert len(errors) == 1
        assert errors[0].get('loc')[0] == 'email'
        assert errors[0].get('msg').endswith('Email already exists')

    def test_professional_data_with_invalid_specialty(self, db_session, professional_data) -> None:
        professional_data.update({
            'password2': professional_data.get('password'),
            'specialty': 'invalid_specialty'
        })
        with pytest.raises(ValidationError) as exception:
            ProfessionalSchema.model_validate(professional_data, context={'db_session': db_session})

        errors = exception.value.errors()
        assert len(errors) == 1
        assert errors[0].get('loc')[0] == 'specialty'
        assert errors[0].get('msg') == "Input should be 'hair_styling', 'hair_coloring', 'makeup_artistry', 'skincare', 'lash_services' or 'nail_services'"


class TestClientManagementEndpoints:
    def test_create_a_client(self, client, client_data, db_session) -> None:
        client_data.update({'password2': client_data.get('password')})
        clients_count = db_session.execute(select(func.count(Client.id))).scalar()
        assert clients_count  == 0

        response = client.post('/api/v1/clients/', json=client_data)
        assert response.status_code == status.HTTP_201_CREATED

        clients_count = db_session.execute(select(func.count(Client.id))).scalar()
        assert clients_count == 1
        user_data = response.json().get('user')

        # Client model tests
        client_id = UUID(user_data.get('id'))
        client = ClientService.get_by_id(db_session, client_id)
        assert client.full_name == client_data.get('full_name')
        assert client.email == client_data.get('email')
        assert client.contact_number == ''
        assert verify_password(client.password, client_data.get('password'))

        # Response tests
        assert user_data.get('full_name') == client_data.get('full_name')
        assert user_data.get('email') == client_data.get('email')
        assert user_data.get('role') == 'client'
        assert user_data.get('contact_number') == client_data.get('contact_number', '')

        tokens = response.json().get('tokens')
        access_token_payload = decode_token(tokens.get('access_token'))
        assert access_token_payload
        assert access_token_payload.get('sub') == user_data.get('id')

        refresh_token_payload = decode_token(tokens.get('refresh_token'))
        assert refresh_token_payload
        assert refresh_token_payload.get('sub') == user_data.get('id')

    def test_client_required_fields(self, client, client_data, assert_validation_error) -> None:
        client_data.update({'password2': client_data.get('password')})

        for field in client_data:
            data = client_data.copy()
            data.pop(field)
            response = client.post('/api/v1/clients/', json=data)
            assert_validation_error(response, field_name=field)

    def test_client_email_should_be_unique(self, client, client_data, db_session, assert_validation_error) -> None:
        user = Client(**client_data)
        db_session.add(user)
        db_session.commit()

        # client with email exists
        assert db_session.query(exists().where(Client.email == client_data.get('email'))).scalar()

        client_data.update({'password2': client_data.get('password')})
        response = client.post('/api/v1/clients/', json=client_data)
        assert_validation_error(response, field_name='email')

    def test_client_password_strength(self, client, client_data, assert_validation_error) -> None:
        client_data.update({'password': '1234', 'password2': '1234'})
        response = client.post('/api/v1/clients/', json=client_data)
        assert_validation_error(response, field_name='password')

    def test_client_passwords_should_be_matching(self, client, client_data, assert_validation_error) -> None:
        client_data.update({'password2': 'Different1234$'})
        assert client_data.get('password') != client_data.get('password2')

        response = client.post('/api/v1/clients/', json=client_data)
        assert_validation_error(response)


class TestProfessionalManagementEndpoints:
    def test_create_a_professional(self, db_session, client, professional_data) -> None:
        professional_data.update({'password2': professional_data.get('password')})

        response = client.post('/api/v1/professionals/', json=professional_data)
        assert response.status_code == status.HTTP_201_CREATED

        # Test created professional
        user_data = response.json().get('user')
        professional_id = UUID(user_data.get('id'))
        professional = ProfessionalService.get_by_id(db_session, professional_id)
        assert professional.full_name == professional_data.get('full_name')
        assert professional.email == professional_data.get('email')
        assert professional.bio == ''
        assert not professional.is_verified
        assert verify_password(professional.password, professional_data.get('password'))

        # Test response
        assert user_data.get('full_name') == professional_data.get('full_name')
        assert user_data.get('email') == professional_data.get('email')
        assert user_data.get('bio') == ''
        assert user_data.get('role') == 'admin'
        assert not user_data.get('is_verified')

        tokens = response.json().get('tokens')
        access_token_payload = decode_token(tokens.get('access_token'))
        assert access_token_payload.get('sub') == user_data.get('id')

        refresh_token_payload = decode_token(tokens.get('refresh_token'))
        assert refresh_token_payload.get('sub') == user_data.get('id')

        # A default schedule is created for professionals
        schedule = db_session.query(Schedule).filter(Schedule.professional == professional).all()
        assert len(schedule) == 7

        weekend = [Schedule.DayOfWeek.SATURDAY, Schedule.DayOfWeek.SUNDAY]
        weekend_schedule = [s for s in schedule if s.day_of_week in weekend]
        weekday_schedule = [s for s in schedule if s.day_of_week not in weekend]
        assert  len(weekend_schedule) == 2
        assert len(weekday_schedule) == 5
        assert all([s.is_available for s in weekday_schedule])
        assert not any([s.is_available for s in weekend_schedule])

    def test_professional_required_fields(self, client, professional_data, assert_validation_error) -> None:
        professional_data.update({'password2': professional_data.get('password')})

        for field in professional_data:
            data = professional_data.copy()
            data.pop(field)

            response = client.post('/api/v1/professionals/', json=data)
            assert_validation_error(response, field_name=field)


    def test_professional_email_should_be_unique(self, client,  db_session, professional_data, assert_validation_error) -> None:
        professional = Professional(**professional_data)
        db_session.add(professional)
        db_session.commit()

        response = client.post('/api/v1/professionals/', json=professional_data)
        assert_validation_error(response, field_name='email')

    def test_professional_invalid_specialty(self, client, professional_data, assert_validation_error) -> None:
        professional_data.update({'password2': professional_data.get('password'), 'specialty': 'invalid'})
        response = client.post('/api/v1/professionals/', json=professional_data)
        assert_validation_error(response, field_name='specialty')


    def test_professional_password_strength(self, client, professional_data, assert_validation_error) -> None:
        professional_data.update({'password': '1234', 'password2': '1234'})
        response = client.post('/api/v1/professionals/', json=professional_data)
        assert_validation_error(response, field_name='password')

    def test_professional_password_should_be_matching(self, client, professional_data, assert_validation_error) -> None:
        professional_data.update({'password2': 'Different1234$'})
        assert professional_data.get('password') != professional_data.get('password2')

        response = client.post('/api/v1/professionals/', json=professional_data)
        assert_validation_error(response)


class TestUserLoginAPIEndpoint:
    def test_login_a_client(self, client, client_data, client_login_data, db_session) -> None:
        user = Client(**client_data)
        db_session.add(user)
        db_session.commit()

        response = client.post('/api/v1/auth/login/', json=client_login_data)
        assert response.status_code == status.HTTP_200_OK

        user_data = response.json().get('user')
        assert user.id == UUID(user_data.get('id'))
        assert user.email == user_data.get('email')
        assert user.contact_number == ''
        assert user_data.get('role') == 'client'

        tokens = response.json().get('tokens')
        access_token_payload = decode_token(tokens.get('access_token'))
        assert access_token_payload.get('sub') == user_data.get('id')

        refresh_token_payload = decode_token(tokens.get('refresh_token'))
        assert refresh_token_payload.get('sub') == user_data.get('id')

    def test_login_a_professional(self, client, db_session, professional_data, professional_login_data) -> None:
        user = Professional(**professional_data)
        db_session.add(user)
        db_session.commit()

        response = client.post('/api/v1/auth/login/', json=professional_login_data)
        assert response.status_code == status.HTTP_200_OK

        user_data = response.json().get('user')
        assert user.id == UUID(user_data.get('id'))
        assert user.email == user_data.get('email')
        assert user.bio == ''
        assert user_data.get('role') == 'admin'

        tokens = response.json().get('tokens')
        access_token_payload = decode_token(tokens.get('access_token'))
        assert access_token_payload.get('sub') == user_data.get('id')

        refresh_token_payload = decode_token(tokens.get('refresh_token'))
        assert refresh_token_payload.get('sub') == user_data.get('id')

    def test_attempt_login_with_invalid_credentials(
            self, client, db_session, client_data, client_login_data, assert_http_error
    ) -> None:

        user = Client(**client_data)
        db_session.add(user)
        db_session.commit()

        # Invalid email address
        data = client_login_data.copy()
        data.update({'email': 'different.email@gmail.com'})
        assert not db_session.query(Client).filter(Client.email == data.get('email')).first()
        assert not db_session.query(Professional).filter(Client.email == data.get('email')).first()

        response = client.post('/api/v1/auth/login/', json=data)
        assert_http_error(response, status_code=status.HTTP_400_BAD_REQUEST, message='Invalid email or password')
