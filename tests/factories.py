import factory
from app.models.user import User
from app.models.company import Company
from app.models.equipment import Equipment

class UserFactory(factory.Factory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    name = factory.Faker('name')
    hashed_password = factory.LazyAttribute(lambda obj: f'hashed_{obj.email}')

class CompanyFactory(factory.Factory):
    class Meta:
        model = Company

    name = factory.Faker('company')
    address = factory.Faker('address')
    admin_user = factory.SubFactory(UserFactory)

class EquipmentFactory(factory.Factory):
    class Meta:
        model = Equipment

    company = factory.SubFactory(CompanyFactory)
    company_id = factory.SelfAttribute('company.id')
    equipment_id = factory.Sequence(lambda n: f'EQ{n:05d}')
    name = factory.Faker('catch_phrase')