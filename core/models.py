
from django.db import models


class Customer(models.Model):
	SEGMENTS = (
		("Gold", "Gold"),
		("Silver", "Silver"),
		("Bronze", "Bronze"),
	)
	name = models.CharField("Nome", max_length=100)
	email = models.EmailField("E-mail", unique=True)
	segment = models.CharField("Segmento", max_length=10, choices=SEGMENTS)
	city = models.CharField("Cidade", max_length=50)
	state = models.CharField("Estado", max_length=30)
	region = models.CharField("Região", max_length=30)
	created_at = models.DateField("Criado em")

	class Meta:
		verbose_name = "Cliente"
		verbose_name_plural = "Clientes"
		indexes = [
			models.Index(fields=["segment", "region"]),
		]

	def __str__(self):
		return f"{self.name} ({self.segment})"


class Product(models.Model):
	name = models.CharField("Nome", max_length=100)
	category = models.CharField("Categoria", max_length=50)
	brand = models.CharField("Marca", max_length=50)
	cost = models.DecimalField("Custo", max_digits=10, decimal_places=2)
	suggested_price = models.DecimalField("Preço Sugerido", max_digits=10, decimal_places=2)

	class Meta:
		verbose_name = "Produto"
		verbose_name_plural = "Produtos"
		indexes = [
			models.Index(fields=["category", "brand"]),
		]

	def __str__(self):
		return f"{self.name} - {self.brand}"


class Order(models.Model):
	STATUS = (
		("Completed", "Completed"),
		("Pending", "Pending"),
		("Cancelled", "Cancelled"),
		("Returned", "Returned"),
	)
	CHANNELS = (
		("Online", "Online"),
		("Store", "Store"),
		("Phone", "Phone"),
		("App", "App"),
	)
	customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="orders")
	order_date = models.DateField("Data do Pedido")
	delivery_date = models.DateField("Data de Entrega")
	status = models.CharField("Status", max_length=10, choices=STATUS)
	channel = models.CharField("Canal", max_length=10, choices=CHANNELS)

	class Meta:
		verbose_name = "Pedido"
		verbose_name_plural = "Pedidos"
		indexes = [
			models.Index(fields=["order_date", "status", "channel"]),
		]

	def __str__(self):
		return f"Order {self.pk} - {self.status}"


class OrderItem(models.Model):
	order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	quantity = models.PositiveIntegerField("Quantidade")
	unit_price = models.DecimalField("Preço Unitário", max_digits=10, decimal_places=2)
	unit_cost = models.DecimalField("Custo Unitário", max_digits=10, decimal_places=2)
	discount_applied = models.DecimalField("Desconto Aplicado", max_digits=5, decimal_places=2, default=0)

	class Meta:
		verbose_name = "Item do Pedido"
		verbose_name_plural = "Itens do Pedido"
		constraints = [
			models.CheckConstraint(condition=models.Q(quantity__gt=0), name="quantity_gt_0"),
			models.CheckConstraint(condition=models.Q(unit_price__gte=0), name="unit_price_gte_0"),
			models.CheckConstraint(condition=models.Q(unit_cost__gte=0), name="unit_cost_gte_0"),
			models.CheckConstraint(condition=models.Q(discount_applied__gte=0), name="discount_gte_0"),
		]
		indexes = [
			models.Index(fields=["order", "product"]),
		]

	def __str__(self):
		return f"Order {self.order_id} - {self.product.name}"
