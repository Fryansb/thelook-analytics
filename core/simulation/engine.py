from typing import List
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction

from core.models import Customer, Product, Order, OrderItem
from core.simulation.events import MarketEventFactory
from core.simulation_constants import (
    SEASONALITY_BASELINE,
    CAGR_ANNUAL_RATE,
    SEGMENT_PURCHASE_FREQUENCY,
    LIFECYCLE_WEIGHTS,
    BLACK_FRIDAY_BASE_MULTIPLIER,
    CHRISTMAS_BOOST_MIN,
    CHRISTMAS_BOOST_MAX,
)


class SimulationEngine:
    """
    Core simulation engine responsible for orchestrating data generation.
    Separates business logic from Django command infrastructure.
    """

    def __init__(self, start_date: date, end_date: date, batch_size: int = 5000):
        self.start_date = start_date
        self.end_date = end_date
        self.batch_size = batch_size
        self.event_factory = MarketEventFactory()

    def calculate_seasonality(self, current_date: date) -> float:
        """Calculate seasonal multiplier for a given date."""
        month = current_date.month
        day = current_date.day

        if month == 11 and 20 <= day <= 30:
            days_into_bf = day - 20
            return BLACK_FRIDAY_BASE_MULTIPLIER + (days_into_bf * 0.2)

        if month == 12:
            return CHRISTMAS_BOOST_MIN + (
                (CHRISTMAS_BOOST_MAX - CHRISTMAS_BOOST_MIN) * (day / 31)
            )

        return SEASONALITY_BASELINE

    def apply_cagr(self, base_volume: float, current_date: date) -> float:
        """Apply Compound Annual Growth Rate to base volume."""
        years_elapsed = (current_date - self.start_date).days / 365.25
        return base_volume * ((1 + CAGR_ANNUAL_RATE) ** years_elapsed)

    def generate_orders_batch(
        self, customers: List[Customer], products: List[Product], current_date: date
    ) -> List[Order]:
        """Generate a batch of orders for a specific date."""
        seasonality = self.calculate_seasonality(current_date)
        base_volume = len(customers) * 0.02
        daily_volume = int(self.apply_cagr(base_volume, current_date) * seasonality)

        market_event = self.event_factory.check_event(current_date)
        if market_event:
            daily_volume = int(daily_volume * market_event.get_multiplier())

        orders = []
        for _ in range(daily_volume):
            customer = self._select_customer_weighted(customers)
            order = Order(
                customer=customer,
                order_date=current_date,
                delivery_date=current_date + timedelta(days=7),
                status="Completed",
                channel="Online",
            )
            orders.append(order)

        return orders

    def _select_customer_weighted(self, customers: List[Customer]) -> Customer:
        """Select customer with segment-based weighting."""
        import random

        weights = [SEGMENT_PURCHASE_FREQUENCY.get(c.segment, 1.0) for c in customers]
        return random.choices(customers, weights=weights, k=1)[0]

    @transaction.atomic
    def save_batch(self, orders: List[Order], products: List[Product]) -> int:
        """Save a batch of orders and items atomically."""
        saved_orders = Order.objects.bulk_create(orders, batch_size=self.batch_size)

        items = []
        for order in saved_orders:
            num_items = self._calculate_items_per_order(order.customer.segment)
            selected_products = self._select_products_weighted(products, num_items)

            for product in selected_products:
                item = OrderItem(
                    order=order,
                    product=product,
                    quantity=1,
                    unit_price=product.suggested_price,
                    unit_cost=product.cost,
                    discount_applied=Decimal("0.00"),
                )
                items.append(item)

        OrderItem.objects.bulk_create(items, batch_size=self.batch_size)
        return len(items)

    def _calculate_items_per_order(self, segment: str) -> int:
        """Calculate number of items based on customer segment."""
        import random

        base_items = {"Premium": 3, "Regular": 2, "Occasional": 1}
        return base_items.get(segment, 2) + random.randint(0, 2)

    def _select_products_weighted(
        self, products: List[Product], count: int
    ) -> List[Product]:
        """Select products with lifecycle-based weighting."""
        import random

        weights = [LIFECYCLE_WEIGHTS.get(p.lifecycle, 1.0) for p in products]
        return random.choices(products, weights=weights, k=count)
