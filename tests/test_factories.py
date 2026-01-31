
import pytest
from tests.factories import CustomerFactory, ProductFactory, OrderFactory, OrderItemFactory

@pytest.mark.django_db
def test_factories_create():
    customer = CustomerFactory()
    product = ProductFactory()
    order = OrderFactory(customer=customer)
    item = OrderItemFactory(order=order, product=product)
    assert str(customer)
    assert str(product)
    assert str(order)
    assert str(item)
