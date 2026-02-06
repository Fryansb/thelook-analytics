"""
Módulo de utilitários para conexão e cache de dados.
Centraliza a lógica de acesso a Redis e PostgreSQL.
"""

from typing import Optional, Dict, Any, List, Tuple
import os
import logging
from datetime import date
import pandas as pd
import redis
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constantes
REDIS_TTL_SECONDS = 86400  # 24 horas
DATE_FORMAT = "%Y-%m-%d"


class DatabaseConfig:
    """Configuração centralizada do banco de dados."""

    @staticmethod
    def get_postgres_url() -> str:
        """Gera URL de conexão PostgreSQL validando variáveis obrigatórias."""
        required_vars = ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB"]
        missing = [var for var in required_vars if not os.environ.get(var)]

        if missing:
            logger.warning(f"Variáveis não configuradas (usando defaults): {missing}")

        user = os.environ.get("POSTGRES_USER", "thelook_user")
        password = os.environ.get("POSTGRES_PASSWORD", "thelook_pass")
        host = os.environ.get("POSTGRES_HOST", "localhost")
        port = int(os.environ.get("POSTGRES_PORT", 5432))
        database = os.environ.get("POSTGRES_DB", "thelook_db")

        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    @staticmethod
    def get_redis_config() -> Dict[str, Any]:
        """Retorna configuração do Redis."""
        return {
            "host": os.environ.get("REDIS_HOST", "localhost"),
            "port": int(os.environ.get("REDIS_PORT", 6379)),
            "decode_responses": True,
            "socket_connect_timeout": 5,
        }


class RedisClient:
    """Cliente Redis singleton com métodos utilitários."""

    _instance: Optional[redis.Redis] = None

    @classmethod
    def get_client(cls) -> Optional[redis.Redis]:
        """Retorna instância singleton do cliente Redis."""
        if cls._instance is None:
            try:
                config = DatabaseConfig.get_redis_config()
                cls._instance = redis.Redis(**config)
                cls._instance.ping()
                logger.info("Redis conectado com sucesso")
            except redis.RedisError as e:
                logger.warning(f"⚠️ Redis não disponível: {e}")
                return None
        return cls._instance

    @classmethod
    def get_metric(
        cls, key: str, date_value: Optional[date] = None, dtype: type = float
    ) -> Optional[Any]:
        """
        Busca métrica do Redis com suporte a data opcional.

        Args:
            key: Prefixo da chave (ex: 'faturamento', 'pedidos_count')
            date_value: Data específica (None = hoje)
            dtype: Tipo de conversão (float, int, str)

        Returns:
            Valor convertido ou None se indisponível
        """
        client = cls.get_client()
        if not client:
            return None

        try:
            if date_value is None:
                date_value = pd.Timestamp.now().date()

            date_str = date_value.strftime(DATE_FORMAT)
            full_key = f"{key}:{date_str}"

            value = client.get(full_key)
            if value is None:
                return 0 if dtype in (int, float) else None

            return dtype(value)
        except (redis.RedisError, ValueError, TypeError) as e:
            logger.error(f"Erro ao buscar {key}: {e}")
            return None

    @classmethod
    def get_top_products(cls, limit: int = 100) -> List[Tuple[str, int]]:
        """
        Busca top N produtos do Redis.

        Args:
            limit: Número máximo de produtos

        Returns:
            Lista de tuplas (nome_produto, quantidade)
        """
        client = cls.get_client()
        if not client:
            return []

        try:
            produtos = client.zrevrange("top_produtos", 0, limit - 1, withscores=True)
            return [
                (p.decode() if isinstance(p, bytes) else p, int(score))
                for p, score in produtos
            ]
        except redis.RedisError as e:
            logger.error(f"Erro ao buscar top produtos: {e}")
            return []

    @classmethod
    def get_regional_sales(cls) -> Dict[str, float]:
        """
        Busca vendas por região do Redis.

        Returns:
            Dicionário {região: valor}
        """
        client = cls.get_client()
        if not client:
            return {}

        regioes = ["Sudeste", "Sul", "Nordeste", "Centro-Oeste", "Norte"]
        vendas = {}

        try:
            for regiao in regioes:
                valor = client.get(f"vendas_regiao:{regiao}")
                vendas[regiao] = float(valor) if valor else 0.0
            return vendas
        except redis.RedisError as e:
            logger.error(f"Erro ao buscar vendas regionais: {e}")
            return {}


class DataLoader:
    """Carregador de dados otimizado do PostgreSQL."""

    _engine: Optional[Engine] = None

    @classmethod
    def get_engine(cls) -> Engine:
        """Retorna engine SQLAlchemy singleton."""
        if cls._engine is None:
            url = DatabaseConfig.get_postgres_url()
            cls._engine = create_engine(
                url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,  # Valida conexões antes de usar
            )
            logger.info("PostgreSQL engine criado")
        return cls._engine

    @classmethod
    def load_tables(
        cls,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Carrega tabelas do banco com queries otimizadas.

        Returns:
            Tupla (orders, items, products, customers)

        Raises:
            Exception: Se houver erro na conexão
        """
        engine = cls.get_engine()

        # Queries otimizadas - apenas colunas necessárias
        queries = {
            "orders": """
                SELECT id, customer_id, order_date, delivery_date, status, channel
                FROM core_order
                WHERE status = 'Completed'
            """,
            "items": """
                SELECT oi.id, oi.order_id, oi.product_id, oi.quantity, oi.unit_price, oi.unit_cost, oi.discount_applied
                FROM core_orderitem oi
                INNER JOIN core_order o ON oi.order_id = o.id
                WHERE o.status = 'Completed'
            """,
            "products": """
                SELECT id, name, category, brand, cost, suggested_price, lifecycle
                FROM core_product
            """,
            "customers": """
                SELECT id, name, email, segment, city, state, region, created_at
                FROM core_customer
            """,
        }

        try:
            orders = pd.read_sql(queries["orders"], engine)
            items = pd.read_sql(queries["items"], engine)
            products = pd.read_sql(queries["products"], engine)
            customers = pd.read_sql(queries["customers"], engine)

            logger.info(f"Dados carregados: {len(orders)} pedidos, {len(items)} itens")
            return orders, items, products, customers

        except Exception as e:
            logger.error(f"❌ Erro ao carregar dados: {e}")
            raise


# Formato de data para helpers
def format_date_key(date_value: Optional[date] = None) -> str:
    """Formata data para chave Redis padronizada."""
    if date_value is None:
        date_value = pd.Timestamp.now().date()
    return date_value.strftime(DATE_FORMAT)
