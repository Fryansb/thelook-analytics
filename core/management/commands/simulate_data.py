
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Customer, Product, Order, OrderItem
from faker import Faker
import random
from datetime import timedelta, date

SEGMENTS = ("Gold", "Silver", "Bronze")
REGIONS = ("Sudeste", "Sul", "Nordeste", "Centro-Oeste", "Norte")
CATEGORIES = ("Eletrônicos", "Roupas", "Casa", "Esporte", "Livros")
BRANDS = ("BrandA", "BrandB", "BrandC", "BrandD", "BrandE")
CHANNELS = ("Online", "Store", "Phone", "App")
STATUS = ("Completed", "Pending", "Cancelled", "Returned")

class Command(BaseCommand):
    help = "Simula dados realistas de e-commerce para Star Schema."

    def add_arguments(self, parser):
        parser.add_argument("--years", type=int, default=2, help="Anos de histórico (default: 2)")


    @transaction.atomic
    def handle(self, *args, **options):
        fake = Faker("pt_BR")
        years = options["years"]
        today = date.today()
        start = date(today.year - years, 1, 1)

        # Garante unicidade de e-mails
        emails = set()
        customers = []
        while len(customers) < 2000:
            email = fake.unique.email()
            if email in emails:
                continue
            emails.add(email)
            customers.append(Customer(
                name=fake.name(),
                email=email,
                segment=random.choices(SEGMENTS, weights=[0.15, 0.35, 0.5])[0],
                city=fake.city(),
                state=fake.estado_sigla(),
                region=random.choice(REGIONS),
                created_at=fake.date_between(start_date=start, end_date=today),
            ))
        Customer.objects.bulk_create(customers, batch_size=500)

        products = [
            Product(
                name=f"Produto {i+1}",
                category=random.choice(CATEGORIES),
                brand=random.choice(BRANDS),
                cost=round(random.uniform(10, 500), 2),
                suggested_price=round(random.uniform(12, 1000), 2),
            )
            for i in range(300)
        ]
        Product.objects.bulk_create(products, batch_size=200)

        # Não faz queries desnecessárias, mantém listas locais
        pareto_products = products[:int(0.2 * len(products))]



        orders = []
        for year in range(today.year - years, today.year + 1):
            base = 5000
            n_orders = int(base * (1.2 ** (year - (today.year - years))))
            for _ in range(n_orders):
                month = random.choices(
                    range(1, 13),
                    weights=[0.7 if m == 2 else 2.0 if m in [11, 12] else 1 for m in range(1, 13)]
                )[0]
                order_date = fake.date_between(start_date=date(year, month, 1), end_date=date(year, month, 28))
                delivery_date = order_date + timedelta(days=random.randint(1, 10))
                status = random.choices(STATUS, weights=[0.85, 0.1, 0.03, 0.02])[0]
                channel = random.choice(CHANNELS)
                customer = random.choice(customers)
                if (today - customer.created_at).days > 365:
                    churn = min(0.5, ((today - customer.created_at).days - 365) / 2000)
                    if random.random() < churn:
                        continue
                orders.append(Order(
                    customer=customer,
                    order_date=order_date,
                    delivery_date=delivery_date,
                    status=status,
                    channel=channel,
                ))
        Order.objects.bulk_create(orders, batch_size=1000)



        items = []
        for order in orders:
            used = set()
            for _ in range(random.randint(1, 5)):
                product = random.choices(
                    population=pareto_products + products,
                    weights=[4]*len(pareto_products) + [1]*len(products),
                    k=1
                )[0]
                if id(product) in used:
                    continue
                used.add(id(product))
                price = round(product.suggested_price * random.uniform(0.9, 1.1), 2)
                discount = random.choices([0, 5, 10, 15], weights=[0.7, 0.15, 0.1, 0.05])[0]
                items.append(OrderItem(
                    order=order,
                    product=product,
                    quantity=random.randint(1, 4),
                    unit_price=price,
                    unit_cost=product.cost,
                    discount_applied=discount,
                ))
        OrderItem.objects.bulk_create(items, batch_size=2000)
        self.stdout.write(self.style.SUCCESS(f"Simulação concluída: {len(orders)} pedidos, {len(items)} itens."))
