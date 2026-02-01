import pytest
from django.db import IntegrityError
from core.models import Customer, Product, Order, OrderItem

@pytest.mark.django_db
def test_orderitem_quantity_gt_0():
    c = Customer.objects.create(name="Ana", email="ana1@email.com", segment="Gold", city="SP", state="SP", region="Sudeste", created_at="2024-01-01")
    p = Product.objects.create(name="Notebook", category="Eletrônicos", brand="BrandA", cost=100, suggested_price=200)
    o = Order.objects.create(customer=c, order_date="2024-01-01", delivery_date="2024-01-02", status="Completed", channel="Online")
    with pytest.raises(IntegrityError):
        OrderItem.objects.create(order=o, product=p, quantity=0, unit_price=200, unit_cost=100, discount_applied=0)

@pytest.mark.django_db
def test_orderitem_unit_price_gte_0():
    c = Customer.objects.create(name="Ana", email="ana2@email.com", segment="Gold", city="SP", state="SP", region="Sudeste", created_at="2024-01-01")
    p = Product.objects.create(name="Notebook", category="Eletrônicos", brand="BrandA", cost=100, suggested_price=200)
    o = Order.objects.create(customer=c, order_date="2024-01-01", delivery_date="2024-01-02", status="Completed", channel="Online")
    with pytest.raises(IntegrityError):
        OrderItem.objects.create(order=o, product=p, quantity=1, unit_price=-1, unit_cost=100, discount_applied=0)

@pytest.mark.django_db
def test_orderitem_unit_cost_gte_0():
    c = Customer.objects.create(name="Ana", email="ana3@email.com", segment="Gold", city="SP", state="SP", region="Sudeste", created_at="2024-01-01")
    p = Product.objects.create(name="Notebook", category="Eletrônicos", brand="BrandA", cost=100, suggested_price=200)
    o = Order.objects.create(customer=c, order_date="2024-01-01", delivery_date="2024-01-02", status="Completed", channel="Online")
    with pytest.raises(IntegrityError):
        OrderItem.objects.create(order=o, product=p, quantity=1, unit_price=200, unit_cost=-1, discount_applied=0)

@pytest.mark.django_db
def test_orderitem_discount_gte_0():
    c = Customer.objects.create(name="Ana", email="ana4@email.com", segment="Gold", city="SP", state="SP", region="Sudeste", created_at="2024-01-01")
    p = Product.objects.create(name="Notebook", category="Eletrônicos", brand="BrandA", cost=100, suggested_price=200)
    o = Order.objects.create(customer=c, order_date="2024-01-01", delivery_date="2024-01-02", status="Completed", channel="Online")
    with pytest.raises(IntegrityError):
        OrderItem.objects.create(order=o, product=p, quantity=1, unit_price=200, unit_cost=100, discount_applied=-5)

@pytest.mark.django_db
def test_customer_required_fields():
    with pytest.raises(Exception):
        Customer.objects.create()

@pytest.mark.django_db
def test_product_required_fields():
    with pytest.raises(Exception):
        Product.objects.create()

@pytest.mark.django_db
def test_order_required_fields():
    with pytest.raises(Exception):
        Order.objects.create()

@pytest.mark.django_db
def test_orderitem_required_fields():
    with pytest.raises(Exception):
        OrderItem.objects.create()
