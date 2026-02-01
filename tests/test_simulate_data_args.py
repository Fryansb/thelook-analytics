import pytest
from django.core.management import call_command
from core.models import Customer, Product, Order, OrderItem

@pytest.mark.django_db
def test_simulate_data_default_args():
    call_command('simulate_data')
    assert Customer.objects.count() > 0
    assert Product.objects.count() > 0
    assert Order.objects.count() > 0
    assert OrderItem.objects.count() > 0

@pytest.mark.django_db
def test_simulate_data_custom_args():
    call_command('simulate_data', '--years=1', '--customers=10', '--products=5')
    assert Customer.objects.count() == 10
    assert Product.objects.count() == 5
    assert Order.objects.count() > 0
    assert OrderItem.objects.count() > 0
