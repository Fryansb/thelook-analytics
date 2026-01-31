import factory
from core.models import Customer, Product, Order, OrderItem
from datetime import date

class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer
    name = factory.Faker('name', locale='pt_BR')
    email = factory.Sequence(lambda n: f'user{n}@mail.com')
    segment = 'Gold'
    city = 'SP'
    state = 'SP'
    region = 'Sudeste'
    created_at = date(2024, 1, 1)

class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product
    name = factory.Sequence(lambda n: f'Produto {n}')
    category = 'Eletrônicos'
    brand = 'BrandA'
    cost = 100
    suggested_price = 200

class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order
    customer = factory.SubFactory(CustomerFactory)
    order_date = date(2024, 1, 1)
    delivery_date = date(2024, 1, 2)
    status = 'Completed'
    channel = 'Online'

class OrderItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrderItem
    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = 1
    unit_price = 200
    unit_cost = 100
    discount_applied = 0
