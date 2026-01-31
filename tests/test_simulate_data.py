import pytest
from django.core.management import call_command
from core.models import Customer, Product, Order, OrderItem

@pytest.mark.django_db
def test_simulate_data_command():
    call_command('simulate_data', '--years=1')
    assert Customer.objects.count() > 0
    assert Product.objects.count() > 0
    assert Order.objects.count() > 0
    assert OrderItem.objects.count() > 0
