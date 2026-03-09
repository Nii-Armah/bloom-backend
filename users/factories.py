from .models import Client, Professional

import random

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


class ProfessionalFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Professional
        sqlalchemy_session = None
        sqlalchemy_session_persistence = 'commit'

    full_name = factory.Faker('name')
    email = factory.Faker('email')
    specialty = factory.LazyFunction(lambda: random.choice([s.value for s in Professional.Specialty]))
    password = 'TestPassword123!'
