from .models import Client

import factory
from factory.alchemy import SQLAlchemyModelFactory


class ClientFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Client
        sqlalchemy_session = None
        sqlalchemy_session_persistence = 'commit'

    full_name = factory.Faker('name')
    email = factory.Faker('email')
    password = 'TestPassword123!'
