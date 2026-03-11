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
    date = datetime.date.today()
    start_time = datetime.time(10, 0, 0)
    end_time = datetime.time(12, 0, 0)
