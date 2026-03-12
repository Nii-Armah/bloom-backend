from users.factories import ProfessionalFactory
from services.models import Service

import factory


class ServiceFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Service

    professional = factory.SubFactory(ProfessionalFactory)
    name = factory.Faker('name')
    price = factory.Faker('pydecimal', left_digits=8, right_digits=2, positive=True)
    duration = factory.Faker('pyint', min_value=1, max_value=100)
