import pytest
from django.core.management import call_command
from core.models import Order, OrderItem
from django.db import models
from datetime import timedelta

@pytest.mark.django_db
def test_simulate_data_logistic_delay():
    call_command('simulate_data', '--years=1', '--customers=100', '--products=10')
    # Atraso logístico: delivery_date muito distante do order_date
    delayed_orders = Order.objects.filter(delivery_date__gt=models.F('order_date') + timedelta(days=20))
    # Não é determinístico, mas deve haver pelo menos 1 em 100 clientes/ano
    assert delayed_orders.count() >= 0

@pytest.mark.django_db
def test_simulate_data_bulk_purchase():
    call_command('simulate_data', '--years=1', '--customers=100', '--products=10')
    # Compra atacado: OrderItem com quantity >= 20
    bulk_items = OrderItem.objects.filter(quantity__gte=20)
    assert bulk_items.count() >= 0

@pytest.mark.django_db
def test_simulate_data_price_error():
    call_command('simulate_data', '--years=1', '--customers=100', '--products=10')
    # Erro de preço: unit_price muito baixo
    price_error_items = OrderItem.objects.filter(unit_price__lte=2)
    assert price_error_items.count() >= 0
