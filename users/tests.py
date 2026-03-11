from .factories import ClientFactory, ProfessionalFactory
from .models import Client, Professional
from .utils import verify_password
from database import init_db
from schedules.models import Schedule
from services.models import Service

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


@pytest.fixture(scope='session')
def client_data():
    return factory.build(dict, FACTORY_CLASS=ClientFactory)


@pytest.fixture(scope='session')
def professional_data():
    return factory.build(dict, FACTORY_CLASS=ProfessionalFactory)


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
