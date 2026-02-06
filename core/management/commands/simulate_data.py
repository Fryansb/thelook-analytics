from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Customer, Product, Order, OrderItem
from core.simulation_constants import *
from faker import Faker
from typing import Optional
import random
import numpy as np
from datetime import timedelta, date, datetime
from tqdm import tqdm
import redis
import os
import logging

# Logging estruturado
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Simula dados sintéticos para Star Schema com crescimento orgânico."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.market_event = None  # Rastrear evento de mercado ativo
        self.event_end_date = None

    def add_arguments(self, parser):
        parser.add_argument(
            "--years", type=int, default=2, help="Anos de histórico (default: 2)"
        )
        parser.add_argument(
            "--customers-per-year",
            type=int,
            default=500,
            help="Clientes novos por ano (média)",
        )
        parser.add_argument(
            "--products-per-year",
            type=int,
            default=50,
            help="Produtos novos por ano (média)",
        )

    def get_seasonality_multiplier(self, current_date: date) -> float:
        """
        Calcula multiplicador de sazonalidade com ruído estocástico.

        Args:
            current_date: Data para calcular sazonalidade

        Returns:
            Multiplicador de sazonalidade (mínimo 0.5x)
        """
        m = 1.0

        # Fim de semana
        if current_date.weekday() >= 5:
            m *= np.random.uniform(WEEKEND_BOOST_MIN, WEEKEND_BOOST_MAX)

        # Black Friday
        if (
            current_date.month == BLACK_FRIDAY_MONTH
            and BLACK_FRIDAY_START_DAY <= current_date.day <= BLACK_FRIDAY_END_DAY
        ):
            m *= (
                np.random.uniform(BLACK_FRIDAY_VARIANCE_MIN, BLACK_FRIDAY_VARIANCE_MAX)
                * BLACK_FRIDAY_BASE_MULTIPLIER
            )

        # Cyber Monday
        elif (
            current_date.month == CYBER_MONDAY_MONTH
            and CYBER_MONDAY_START_DAY <= current_date.day <= CYBER_MONDAY_END_DAY
            and current_date.weekday() == 0
        ):
            m *= np.random.uniform(CYBER_MONDAY_BOOST_MIN, CYBER_MONDAY_BOOST_MAX)

        # Natal
        elif (
            current_date.month == CHRISTMAS_MONTH
            and CHRISTMAS_START_DAY <= current_date.day <= CHRISTMAS_END_DAY
        ):
            m *= np.random.uniform(CHRISTMAS_BOOST_MIN, CHRISTMAS_BOOST_MAX)

        # Pós-Natal
        elif (
            current_date.month == CHRISTMAS_MONTH
            and current_date.day >= POST_CHRISTMAS_START_DAY
        ):
            m *= np.random.uniform(
                POST_CHRISTMAS_REDUCTION_MIN, POST_CHRISTMAS_REDUCTION_MAX
            )

        # Janeiro - Período fraco
        elif current_date.month == JANUARY_MONTH:
            m *= np.random.uniform(JANUARY_REDUCTION_MIN, JANUARY_REDUCTION_MAX)

        # Aniversário da empresa
        elif current_date.month == COMPANY_ANNIVERSARY_MONTH:
            m *= np.random.uniform(
                COMPANY_ANNIVERSARY_BOOST_MIN, COMPANY_ANNIVERSARY_BOOST_MAX
            )

        return max(m, MIN_SEASONALITY_MULTIPLIER)

    def apply_cagr(
        self, base_volume: float, start_date: date, current_date: date
    ) -> float:
        """
        Aplica taxa de crescimento anual composto (CAGR).

        Args:
            base_volume: Volume base inicial
            start_date: Data de início
            current_date: Data atual

        Returns:
            Volume ajustado pelo crescimento
        """
        days_elapsed = (current_date - start_date).days
        years_elapsed = days_elapsed / DAYS_PER_YEAR
        growth_factor = (1 + CAGR_ANNUAL_RATE) ** years_elapsed
        return base_volume * growth_factor

    def check_market_event(self, current_date: date) -> Optional[str]:
        """
        Simula choques de mercado aleatórios.

        Args:
            current_date: Data atual

        Returns:
            Tipo de evento ou None
        """
        # Se já tem evento ativo, continua até fim
        if (
            self.market_event
            and self.event_end_date
            and current_date < self.event_end_date
        ):
            return self.market_event

        # Chance de novo evento
        if random.random() < MARKET_EVENT_PROBABILITY:
            event_type = random.choice(MARKET_EVENTS)
            duration = random.randint(
                MARKET_EVENT_MIN_DURATION, MARKET_EVENT_MAX_DURATION
            )
            self.event_end_date = current_date + timedelta(days=duration)
            self.market_event = event_type
            return event_type

        # Sem evento
        self.market_event = None
        return None

    def apply_market_event(
        self, multiplier: float, market_event: Optional[str]
    ) -> float:
        """
        Aplica efeito do evento de mercado ao multiplicador.

        Args:
            multiplier: Multiplicador base
            market_event: Tipo de evento ou None

        Returns:
            Multiplicador ajustado
        """
        if market_event is None:
            return multiplier

        return multiplier * EVENT_MULTIPLIERS.get(market_event, 1.0)

    def get_product_weight(self, product_lifecycle: str) -> float:
        """
        Retorna peso do produto baseado em seu ciclo de vida.

        Args:
            product_lifecycle: Ciclo de vida do produto

        Returns:
            Peso para seleção ponderada
        """
        return LIFECYCLE_WEIGHTS.get(product_lifecycle, 1.0)

    @transaction.atomic
    def handle(self, *args, **options):
        fake = Faker("pt_BR")
        # Seed para reprodutibilidade
        Faker.seed(42)
        np.random.seed(42)
        random.seed(42)

        # Conexão com Redis
        redis_host = os.environ.get("REDIS_HOST", "localhost")
        redis_port = int(os.environ.get("REDIS_PORT", 6379))
        redis_client = redis.Redis(
            host=redis_host, port=redis_port, decode_responses=True
        )

        years = options["years"]
        customers_per_year = options["customers_per_year"]
        products_per_year = options["products_per_year"]

        today = date.today()
        start_date = date(today.year - years, 1, 1)

        self.stdout.write(self.style.WARNING("🧹 Limpando dados antigos..."))
        # Limpeza em ordem correta devido a Foreign Keys
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Product.objects.all().delete()
        Customer.objects.all().delete()

        # Estruturas para crescimento orgânico
        all_customers = []
        all_products = []
        customer_metadata = {}
        product_metadata = {}

        self.stdout.write("🌱 Simulando crescimento orgânico ao longo do tempo...")

        # Para cada ano, adicionar novos produtos e clientes
        for year_offset in range(years):
            year_date = date(start_date.year + year_offset, 1, 1)

            # Produtos novos por ano (com variação +/- 20%)
            num_new_products = int(products_per_year * random.uniform(0.8, 1.2))
            self.stdout.write(f"  Ano {year_date.year}: +{num_new_products} produtos")

            for _ in range(num_new_products):
                cat = random.choice(CATEGORIES)
                if cat == "Eletrônicos":
                    price = random.uniform(500, 5000)
                elif cat == "Roupas":
                    price = random.uniform(40, 300)
                else:
                    price = random.uniform(50, 1000)

                # Atribuir lifecycle ao produto
                lifecycle = np.random.choice(
                    ["Stable", "Viral", "Obsolete"], p=[0.7, 0.2, 0.1]
                )

                p = Product(
                    name=f"{cat} - {fake.word().title()} {fake.color_name()}",
                    category=cat,
                    brand=fake.company(),
                    cost=round(price * 0.6, 2),
                    suggested_price=round(price, 2),
                    lifecycle=lifecycle,
                )
                all_products.append(p)

                product_metadata[len(all_products) - 1] = {
                    "lifecycle": lifecycle,
                    "launch_date": year_date,
                }

            # Clientes novos por ano (com variação +/- 30%)
            num_new_customers = int(customers_per_year * random.uniform(0.7, 1.3))
            self.stdout.write(
                f"  👥 Ano {year_date.year}: +{num_new_customers} clientes"
            )

            for _ in range(num_new_customers):
                # Data de cadastro ao longo do ano
                created_at = fake.date_between(
                    start_date=year_date,
                    end_date=min(date(year_date.year, 12, 31), today),
                )

                # Distribuição de personas mais realista
                # 70% compram 1-2x, 20% moderados, 10% VIPs
                persona = np.random.choice(
                    ["OneTime", "Leal", "VIP"], p=[0.70, 0.20, 0.10]
                )

                c = Customer(
                    name=fake.name(),
                    email=fake.unique.email(),
                    segment=random.choice(SEGMENTS),
                    city=fake.city(),
                    state=fake.estado_sigla(),
                    region=random.choice(REGIONS),
                    created_at=created_at,
                )
                all_customers.append(c)
                customer_metadata[len(all_customers) - 1] = {
                    "persona": persona,
                    "created_at": created_at,
                    "max_purchases": (
                        random.randint(30, 100)
                        if persona == "OneTime"
                        else (
                            random.randint(100, 300)
                            if persona == "Leal"
                            else random.randint(500, 1500)
                        )
                    ),
                    "purchase_count": 0,
                }

        # Bulk Create
        self.stdout.write(
            f"Salvando {len(all_products)} produtos e {len(all_customers)} clientes..."
        )
        created_products = Product.objects.bulk_create(all_products)
        created_customers = Customer.objects.bulk_create(all_customers)

        # 3. Motor de vendas temporal
        self.stdout.write("Simulando vendas dia a dia (Engine de Realidade)...")

        orders_objs = []
        order_items_objs = []

        total_days = (today - start_date).days
        current_date = start_date
        num_products_total = len(created_products)

        with tqdm(total=total_days) as pbar:
            while current_date <= today:
                # 1. Sazonalidade com ruído estocástico
                seasonality = self.get_seasonality_multiplier(current_date)

                # 2. Aplicar CAGR (crescimento anual composto)
                base_volume = 30
                with_cagr = self.apply_cagr(base_volume, start_date, current_date)

                # 3. Verificar evento de mercado
                market_event = self.check_market_event(current_date)
                multiplier = seasonality * (with_cagr / base_volume)
                multiplier = self.apply_market_event(multiplier, market_event)

                # Gerar volume diário com Poisson (realista)
                daily_volume = np.random.poisson(multiplier * 30)

                # Log de eventos para debug
                if market_event:
                    self.stdout.write(
                        f"  {current_date}: {market_event.upper()} evento de mercado"
                    )

                if daily_volume > 0:
                    # Seleciona clientes válidos
                    valid_indices = [
                        idx
                        for idx, meta in customer_metadata.items()
                        if meta["created_at"] <= current_date
                        and meta["purchase_count"] < meta["max_purchases"]
                    ]

                    if valid_indices:
                        # Calcular pesos considerando personas E lifecycle do produto
                        weights = []
                        for idx in valid_indices:
                            persona = customer_metadata[idx]["persona"]
                            # Peso por persona
                            if persona == "VIP":
                                w = 15
                            elif persona == "Leal":
                                w = 5
                            else:
                                w = 1
                            weights.append(w)

                        probs = np.array(weights) / sum(weights)

                        # Escolhe clientes compradores do dia
                        buyer_indices = np.random.choice(
                            valid_indices,
                            size=min(daily_volume, len(valid_indices)),
                            p=probs,
                            replace=False,
                        )

                        for cust_idx in buyer_indices:
                            customer = created_customers[cust_idx]
                            persona = customer_metadata[cust_idx]["persona"]

                            # Incrementa contador de compras
                            customer_metadata[cust_idx]["purchase_count"] += 1

                            # Criação do pedido
                            status = np.random.choice(STATUS, p=[0.75, 0.1, 0.1, 0.05])
                            delivery_days = random.randint(2, 10)

                            # Anomalia: atraso logístico (0.5% chance)
                            if random.random() < 0.005:
                                delivery_days = random.randint(30, 90)

                            # Calcula a data de entrega
                            calculated_delivery_date = current_date + timedelta(
                                days=delivery_days
                            )

                            order = Order(
                                customer=customer,
                                order_date=current_date,
                                delivery_date=calculated_delivery_date,
                                status=status,
                                channel=random.choice(CHANNELS),
                            )
                            orders_objs.append(order)

                            # Itens do pedido
                            if persona == "VIP":
                                n_items = random.randint(2, 6)
                            else:
                                n_items = random.randint(1, 3)

                            # Anomalia: compra atacado B2B (0.2% chance)
                            if random.random() < 0.002:
                                n_items = 1
                                bulk_qty = random.randint(20, 50)
                            else:
                                bulk_qty = None

                            for _ in range(n_items):
                                # Seleciona produto considerando seu lifecycle
                                product_weights = []
                                for prod in created_products:
                                    weight = self.get_product_weight(prod.lifecycle)
                                    product_weights.append(weight)

                                probs_products = np.array(product_weights) / sum(
                                    product_weights
                                )
                                prod_idx = np.random.choice(
                                    len(created_products), p=probs_products
                                )
                                product = created_products[prod_idx]

                                qty = bulk_qty if bulk_qty else random.randint(1, 3)
                                price = float(product.suggested_price)

                                # Anomalia: erro de preço (0.2% chance)
                                if random.random() < 0.002:
                                    price = 1.99

                                item = OrderItem(
                                    order=order,
                                    product=product,
                                    quantity=qty,
                                    unit_price=price,
                                    unit_cost=product.cost,
                                    discount_applied=random.choice([0, 0, 5, 10]),
                                )
                                order.temp_items = (
                                    order.temp_items + [item]
                                    if hasattr(order, "temp_items")
                                    else [item]
                                )

                current_date += timedelta(days=1)
                pbar.update(1)

        # 4. Salvando pedidos e itens
        self.stdout.write("Salvando pedidos no banco (pode demorar)...")

        # Salva Orders primeiro para gerar IDs
        saved_orders = Order.objects.bulk_create(orders_objs, batch_size=2000)

        self.stdout.write("🔗 Vinculando Itens...")
        all_items_to_save = []

        # O bulk_create do Django pode não retornar IDs em todas as versões/DBs

        # Reatribuição simples (assumindo paridade de lista)
        for i, order in enumerate(saved_orders):
            # Recupera os itens temporários anexados
            original_obj = orders_objs[i]
            if hasattr(original_obj, "temp_items"):
                for item in original_obj.temp_items:
                    item.order = order
                    all_items_to_save.append(item)

        self.stdout.write("Salvando itens no banco...")
        OrderItem.objects.bulk_create(all_items_to_save, batch_size=5000)

        self.stdout.write(
            self.style.SUCCESS(
                f"Sucesso! Gerados {len(saved_orders)} pedidos e {len(all_items_to_save)} itens."
            )
        )

        # Atualiza agregações no Redis usando queries otimizadas
        self.stdout.write("Atualizando agregações no Redis...")

        from django.db.models import Sum, Count, F
        from django.db.models.functions import TruncDate
        from collections import defaultdict

        hoje_str = today.strftime("%Y-%m-%d")

        # Agregação por dia com query otimizada - APENAS PEDIDOS COMPLETED
        aggregated_by_day = (
            OrderItem.objects.select_related("order", "order__customer", "product")
            .filter(order__status="Completed")
            .annotate(
                order_date=TruncDate("order__order_date"),
                faturamento=F("unit_price") * F("quantity"),
            )
            .values("order_date")
            .annotate(
                total_faturamento=Sum("faturamento"),
                total_pedidos=Count("order_id", distinct=True),
            )
        )

        # Top produtos - APENAS PEDIDOS COMPLETED
        vendas_por_produto = (
            OrderItem.objects.filter(order__status="Completed")
            .values("product__name")
            .annotate(total_qty=Sum("quantity"))
            .order_by("-total_qty")
        )

        # Vendas por região - APENAS PEDIDOS COMPLETED
        vendas_por_regiao = (
            OrderItem.objects.filter(order__status="Completed")
            .select_related("order__customer")
            .annotate(faturamento=F("unit_price") * F("quantity"))
            .values("order__customer__region")
            .annotate(total=Sum("faturamento"))
        )

        # Clientes ativos hoje - APENAS PEDIDOS COMPLETED
        clientes_ativos_hoje = set(
            OrderItem.objects.filter(
                order__status="Completed",
                order__order_date__gte=today,
                order__order_date__lt=today + timedelta(days=1),
            )
            .values_list("order__customer_id", flat=True)
            .distinct()
        )

        pipe = redis_client.pipeline()

        # Atualizar faturamento e pedidos por dia
        for item in aggregated_by_day:
            dia_str = item["order_date"].strftime("%Y-%m-%d")
            pipe.set(
                f"faturamento:{dia_str}", float(item["total_faturamento"]), ex=86400
            )
            pipe.set(f"pedidos_count:{dia_str}", item["total_pedidos"], ex=86400)

        # Top produtos
        pipe.delete("top_produtos")
        for item in vendas_por_produto:
            pipe.zadd("top_produtos", {item["product__name"]: item["total_qty"]})
        pipe.expire("top_produtos", 86400)

        # Vendas por região
        for item in vendas_por_regiao:
            regiao = item["order__customer__region"]
            if regiao:
                pipe.set(f"vendas_regiao:{regiao}", float(item["total"]), ex=86400)

        # Clientes ativos hoje
        pipe.set(f"clientes_ativos:{hoje_str}", len(clientes_ativos_hoje), ex=86400)

        pipe.execute()

        self.stdout.write(self.style.SUCCESS("Agregações atualizadas no Redis."))

        pipe.set(f"clientes_ativos:{hoje_str}", len(clientes_ativos_hoje), ex=86400)

        pipe.execute()

        self.stdout.write(self.style.SUCCESS("Agregações atualizadas no Redis."))
