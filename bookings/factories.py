from .models import Booking
from services.factories import ServiceFactory
from users.factories import ClientFactory, ProfessionalFactory

import datetime

import factory


class BookingFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Booking

    client = factory.SubFactory(ClientFactory)
    professional = factory.SubFactory(ProfessionalFactory)
    service = factory.SubFactory(ServiceFactory)
    start = datetime.datetime.now()
    end = datetime.datetime.now() + datetime.timedelta(minutes=45)
