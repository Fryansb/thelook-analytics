import pytest
from core.models import Customer, Product, Order, OrderItem

@pytest.mark.django_db
def test_customer_str():
    c = Customer(name="Ana", email="ana@email.com", segment="Gold", city="SP", state="SP", region="Sudeste", created_at="2024-01-01")
    assert str(c) == "Ana (Gold)"

@pytest.mark.django_db
def test_product_str():
    p = Product(name="Notebook", category="Eletrônicos", brand="BrandA", cost=100, suggested_price=200)
    assert str(p) == "Notebook - BrandA"

@pytest.mark.django_db
def test_orderitem_str():
    c = Customer.objects.create(name="Ana", email="ana@email.com", segment="Gold", city="SP", state="SP", region="Sudeste", created_at="2024-01-01")
    p = Product.objects.create(name="Notebook", category="Eletrônicos", brand="BrandA", cost=100, suggested_price=200)
    o = Order.objects.create(customer=c, order_date="2024-01-01", delivery_date="2024-01-02", status="Completed", channel="Online")
    item = OrderItem(order=o, product=p, quantity=1, unit_price=200, unit_cost=100, discount_applied=0)
    assert str(item) == f"Order {o.id} - {p.name}"
