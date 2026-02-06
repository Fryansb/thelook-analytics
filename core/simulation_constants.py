"""
Constantes para simula\u00e7\u00e3o de dados de e-commerce.
Centraliza magic numbers e configura\u00e7\u00f5es de neg\u00f3cio.
"""

# =============================================================================
# CONFIGURA\u00c7\u00d5ES DE NEG\u00d3CIO
# =============================================================================

# Segmentos de clientes
SEGMENTS = ("Gold", "Silver", "Bronze")

# Regi\u00f5es brasileiras
REGIONS = ("Sudeste", "Sul", "Nordeste", "Centro-Oeste", "Norte")

# Categorias de produtos
CATEGORIES = ("Eletr\u00f4nicos", "Roupas", "Casa", "Esporte", "Livros")

# Canais de venda
CHANNELS = ("Online", "Store", "Phone", "App")

# Status de pedidos
STATUS = ("Completed", "Pending", "Cancelled", "Returned")

# =============================================================================
# SAZONALIDADE
# =============================================================================

# Fim de semana
WEEKEND_BOOST_MIN = 1.0
WEEKEND_BOOST_MAX = 1.3

# Black Friday
BLACK_FRIDAY_MONTH = 11
BLACK_FRIDAY_START_DAY = 20
BLACK_FRIDAY_END_DAY = 30
BLACK_FRIDAY_BASE_MULTIPLIER = 3.5
BLACK_FRIDAY_VARIANCE_MIN = 0.7
BLACK_FRIDAY_VARIANCE_MAX = 1.2

# Cyber Monday
CYBER_MONDAY_MONTH = 12
CYBER_MONDAY_START_DAY = 1
CYBER_MONDAY_END_DAY = 7
CYBER_MONDAY_BOOST_MIN = 2.0
CYBER_MONDAY_BOOST_MAX = 3.5

# Natal
CHRISTMAS_MONTH = 12
CHRISTMAS_START_DAY = 10
CHRISTMAS_END_DAY = 24
CHRISTMAS_BOOST_MIN = 1.5
CHRISTMAS_BOOST_MAX = 2.5

# P\u00f3s-Natal
POST_CHRISTMAS_START_DAY = 25
POST_CHRISTMAS_END_DAY = 31
POST_CHRISTMAS_REDUCTION_MIN = 0.1
POST_CHRISTMAS_REDUCTION_MAX = 0.4

# Janeiro (per\u00edodo fraco)
JANUARY_MONTH = 1
JANUARY_REDUCTION_MIN = 0.4
JANUARY_REDUCTION_MAX = 0.8

# Anivers\u00e1rio da empresa (Maio)
COMPANY_ANNIVERSARY_MONTH = 5
COMPANY_ANNIVERSARY_BOOST_MIN = 1.2
COMPANY_ANNIVERSARY_BOOST_MAX = 1.8

# M\u00ednimo multiplicador de sazonalidade
MIN_SEASONALITY_MULTIPLIER = 0.5

# =============================================================================
# CRESCIMENTO ORGÂNICO (CAGR)
# =============================================================================

CAGR_ANNUAL_RATE = 0.12  # 12% ao ano
DAYS_PER_YEAR = 365.25

# =============================================================================
# EVENTOS DE MERCADO
# =============================================================================

# Probabilidade di\u00e1ria de evento de mercado
MARKET_EVENT_PROBABILITY = 0.005  # 0.5% ao dia

# Tipos de eventos
MARKET_EVENT_VIRAL = "viral"
MARKET_EVENT_MARKETING = "marketing"
MARKET_EVENT_SITE_DOWN = "site_down"
MARKET_EVENT_LOGISTICS_CRISIS = "logistics_crisis"

MARKET_EVENTS = [
    MARKET_EVENT_VIRAL,
    MARKET_EVENT_MARKETING,
    MARKET_EVENT_SITE_DOWN,
    MARKET_EVENT_LOGISTICS_CRISIS,
]

# Dura\u00e7\u00e3o de eventos (dias)
MARKET_EVENT_MIN_DURATION = 3
MARKET_EVENT_MAX_DURATION = 7

# Multiplicadores de eventos
EVENT_MULTIPLIERS = {
    MARKET_EVENT_VIRAL: 2.0,  # Dobra volume
    MARKET_EVENT_MARKETING: 1.8,  # +80%
    MARKET_EVENT_SITE_DOWN: 0.3,  # Cai 70%
    MARKET_EVENT_LOGISTICS_CRISIS: 0.5,  # Cai 50%
}

# =============================================================================
# CICLO DE VIDA DE PRODUTOS
# =============================================================================

LIFECYCLE_STABLE = "Stable"
LIFECYCLE_VIRAL = "Viral"
LIFECYCLE_OBSOLETE = "Obsolete"

# Distribui\u00e7\u00e3o de lifecycle
LIFECYCLE_DISTRIBUTION = [LIFECYCLE_STABLE, LIFECYCLE_VIRAL, LIFECYCLE_OBSOLETE]
LIFECYCLE_PROBABILITIES = [0.7, 0.2, 0.1]  # 70% stable, 20% viral, 10% obsoleto

# Pesos para sele\u00e7\u00e3o de produtos por lifecycle
LIFECYCLE_WEIGHTS = {
    LIFECYCLE_VIRAL: 5.0,
    LIFECYCLE_STABLE: 1.0,
    LIFECYCLE_OBSOLETE: 0.1,
}

# =============================================================================
# PERSONAS DE CLIENTES
# =============================================================================

PERSONA_ONE_TIME = "OneTime"
PERSONA_LEAL = "Leal"
PERSONA_VIP = "VIP"

# Distribui\u00e7\u00e3o de personas
PERSONAS = [PERSONA_ONE_TIME, PERSONA_LEAL, PERSONA_VIP]
PERSONA_PROBABILITIES = [0.70, 0.20, 0.10]  # 70% one-time, 20% leal, 10% VIP

# Faixas de compras por persona
PERSONA_PURCHASE_RANGES = {
    PERSONA_ONE_TIME: (30, 100),
    PERSONA_LEAL: (100, 300),
    PERSONA_VIP: (500, 1500),
}

# =============================================================================
# VARIA\u00c7\u00c3O DE PRODUTOS E CLIENTES
# =============================================================================

PRODUCT_VARIATION_MIN = 0.8
PRODUCT_VARIATION_MAX = 1.2

CUSTOMER_VARIATION_MIN = 0.7
CUSTOMER_VARIATION_MAX = 1.3

# =============================================================================
# PRE\u00c7OS POR CATEGORIA
# =============================================================================

PRICE_RANGES = {
    "Eletr\u00f4nicos": (500, 5000),
    "Roupas": (40, 300),
    "Casa": (50, 1000),
    "Esporte": (50, 1000),
    "Livros": (50, 1000),
}

# Margem de custo (60% do pre\u00e7o)
COST_MARGIN = 0.6

# =============================================================================
# VOLUME DE VENDAS
# =============================================================================

BASE_DAILY_VOLUME = 30  # Volume base de pedidos por dia
POISSON_BASE_MULTIPLIER = 30  # Multiplicador para distribui\u00e7\u00e3o Poisson

# =============================================================================
# REDIS
# =============================================================================

REDIS_TTL_SECONDS = 86400  # 24 horas

# =============================================================================
# MAPEAMENTO GEOGRÁFICO
# =============================================================================

UF_TO_REGION_MAP = {
    "AC": "Norte",
    "AP": "Norte",
    "AM": "Norte",
    "PA": "Norte",
    "RO": "Norte",
    "RR": "Norte",
    "TO": "Norte",
    "AL": "Nordeste",
    "BA": "Nordeste",
    "CE": "Nordeste",
    "MA": "Nordeste",
    "PB": "Nordeste",
    "PE": "Nordeste",
    "PI": "Nordeste",
    "RN": "Nordeste",
    "SE": "Nordeste",
    "DF": "Centro-Oeste",
    "GO": "Centro-Oeste",
    "MT": "Centro-Oeste",
    "MS": "Centro-Oeste",
    "ES": "Sudeste",
    "MG": "Sudeste",
    "RJ": "Sudeste",
    "SP": "Sudeste",
    "PR": "Sul",
    "RS": "Sul",
    "SC": "Sul",
}

# =============================================================================
# BULK OPERATIONS
# =============================================================================

BULK_CREATE_BATCH_SIZE = 5000
