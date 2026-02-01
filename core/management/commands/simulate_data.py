from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Customer, Product, Order, OrderItem
from faker import Faker
import random
import numpy as np
from datetime import timedelta, date, datetime
from tqdm import tqdm

SEGMENTS = ("Gold", "Silver", "Bronze")
REGIONS = ("Sudeste", "Sul", "Nordeste", "Centro-Oeste", "Norte")
CATEGORIES = ("Eletrônicos", "Roupas", "Casa", "Esporte", "Livros")
CHANNELS = ("Online", "Store", "Phone", "App")
STATUS = ("Completed", "Pending", "Cancelled", "Returned")

class Command(BaseCommand):
    help = "Simula dados sintéticos para Star Schema."

    def add_arguments(self, parser):
        parser.add_argument("--years", type=int, default=2, help="Anos de histórico (default: 2)")
        parser.add_argument("--customers", type=int, default=2000, help="Qtd de clientes")
        parser.add_argument("--products", type=int, default=150, help="Qtd de produtos")

    def get_seasonality_multiplier(self, current_date):
        """Retorna multiplicador de demanda baseado na data (Sazonalidade Real)."""
        m = 1.0
        # Fim de semana
        if current_date.weekday() >= 5: m *= 1.15
        
        # Black Friday
        if current_date.month == 11:
            m *= 1.5
            if current_date.day >= 20: m *= 3.5
        # Natal
        elif current_date.month == 12:
            m *= 2.0
            if current_date.day > 23: m *= 0.2
        # Janeiro
        elif current_date.month == 1:
            m *= 0.6
            
        return m

    @transaction.atomic
    def handle(self, *args, **options):
        fake = Faker("pt_BR")
        # Seed para reprodutibilidade
        Faker.seed(42)
        np.random.seed(42)
        random.seed(42)

        years = options["years"]
        num_customers = options["customers"]
        num_products = options["products"]

        today = date.today()
        start_date = date(today.year - years, 1, 1)

        self.stdout.write(self.style.WARNING("🧹 Limpando dados antigos..."))
        # Limpeza em ordem correta devido a Foreign Keys
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Product.objects.all().delete()
        Customer.objects.all().delete()

        # 1. Produtos
        self.stdout.write("📦 Gerando Produtos...")
        products_objs = []
        product_metadata = {}

        for i in range(num_products):
            cat = random.choice(CATEGORIES)
            if cat == 'Eletrônicos': price = random.uniform(500, 5000)
            elif cat == 'Roupas': price = random.uniform(40, 300)
            else: price = random.uniform(50, 1000)
            
            p = Product(
                name=f"{cat} - {fake.word().title()} {fake.color_name()}",
                category=cat,
                brand=fake.company(),
                cost=round(price * 0.6, 2),
                suggested_price=round(price, 2),
            )
            products_objs.append(p)
            
            lifecycle = np.random.choice(['Stable', 'Viral', 'Obsolete'], p=[0.7, 0.2, 0.1])
            product_metadata[i] = {'lifecycle': lifecycle, 'obj_index': i}

        # Bulk Create salva no banco
        created_products = Product.objects.bulk_create(products_objs)

        # 2. Clientes
        self.stdout.write("👥 Gerando Clientes com Personas...")
        customers_objs = []
        customer_metadata = {}
        
        emails = set()
        
        for i in range(num_customers):
            email = fake.unique.email()
            created_at = fake.date_between(start_date=start_date, end_date=today)
            
            persona = np.random.choice(['Novo', 'Leal', 'VIP'], p=[0.6, 0.3, 0.1])
            
            c = Customer(
                name=fake.name(),
                email=email,
                segment=random.choice(SEGMENTS),
                city=fake.city(),
                state=fake.estado_sigla(),
                region=random.choice(REGIONS),
                created_at=created_at
            )
            customers_objs.append(c)
            customer_metadata[i] = {'persona': persona, 'created_at': created_at}

        created_customers = Customer.objects.bulk_create(customers_objs)

        # 3. Motor de vendas temporal
        self.stdout.write("🚀 Simulando vendas dia a dia (Engine de Realidade)...")
        
        orders_objs = []
        order_items_objs = []
        
        total_days = (today - start_date).days
        current_date = start_date
        
        # Mapeamento rápido de ID para objeto
        
        with tqdm(total=total_days) as pbar:
            while current_date <= today:
                # Sazonalidade (volume diário)
                multiplier = self.get_seasonality_multiplier(current_date)
                daily_volume = np.random.poisson(30 * multiplier)

                if daily_volume > 0:
                    # Seleção de clientes ativos
                    valid_indices = [
                        idx for idx, meta in customer_metadata.items() 
                        if meta['created_at'] <= current_date
                    ]
                    
                    if valid_indices:
                        weights = []
                        for idx in valid_indices:
                            p = customer_metadata[idx]['persona']
                            if p == 'VIP': w = 15
                            elif p == 'Leal': w = 5
                            else: w = 1
                            weights.append(w)
                        
                        probs = np.array(weights) / sum(weights)
                        
                        # Escolhe clientes compradores do dia
                        buyer_indices = np.random.choice(valid_indices, size=min(daily_volume, len(valid_indices)), p=probs, replace=True)

                        for cust_idx in buyer_indices:
                            customer = created_customers[cust_idx]
                            persona = customer_metadata[cust_idx]['persona']

                            # Criação do pedido
                            status = np.random.choice(STATUS, p=[0.75, 0.1, 0.1, 0.05])
                            delivery_days = random.randint(2, 10)

                            # Anomalia: atraso logístico (0.5% chance)
                            if random.random() < 0.005:
                                delivery_days = random.randint(30, 90)

                            # Calcula a data de entrega
                            calculated_delivery_date = current_date + timedelta(days=delivery_days)

                            order = Order(
                                customer=customer,
                                order_date=current_date,
                                delivery_date=calculated_delivery_date,
                                status=status,
                                channel=random.choice(CHANNELS)
                            )
                            orders_objs.append(order)

                            # Itens do pedido
                            if persona == 'VIP':
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
                                # Escolhe produto
                                prod_idx = random.randint(0, num_products - 1)
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
                                    discount_applied=random.choice([0, 0, 5, 10])
                                )
                                order.temp_items = order.temp_items + [item] if hasattr(order, 'temp_items') else [item]

                current_date += timedelta(days=1)
                pbar.update(1)

        # 4. Salvando pedidos e itens
        self.stdout.write("💾 Salvando Pedidos no Banco (Isso pode demorar)...")
        
        # Salva Orders primeiro para gerar IDs
        saved_orders = Order.objects.bulk_create(orders_objs, batch_size=2000)
        
        self.stdout.write("🔗 Vinculando Itens...")
        all_items_to_save = []
        
        # O bulk_create do Django pode não retornar IDs em todas as versões/DBs
        
        # Reatribuição simples (assumindo paridade de lista)
        for i, order in enumerate(saved_orders):
            # Recupera os itens temporários anexados
            original_obj = orders_objs[i]
            if hasattr(original_obj, 'temp_items'):
                for item in original_obj.temp_items:
                    item.order = order
                    all_items_to_save.append(item)

        self.stdout.write("💾 Salvando Itens no Banco...")
        OrderItem.objects.bulk_create(all_items_to_save, batch_size=5000)

        self.stdout.write(self.style.SUCCESS(f"✅ Sucesso! Gerados {len(saved_orders)} pedidos e {len(all_items_to_save)} itens."))