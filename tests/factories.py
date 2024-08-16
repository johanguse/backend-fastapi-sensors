import factory
from app.models.user import User

class UserFactory(factory.Factory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    name = factory.Faker('name')
    hashed_password = factory.LazyAttribute(lambda obj: f'hashed_{obj.email}')
