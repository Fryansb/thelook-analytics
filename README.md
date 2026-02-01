# E-commerce Data Generator

[![Django CI](https://github.com/Fryansb/ecommerce-data-generator/workflows/Django%20CI/badge.svg)](https://github.com/Fryansb/ecommerce-data-generator/actions)

Sistema de geração de dados realistas de e-commerce para análise de dados, com dashboard Streamlit interativo e integração com Superset.

## 🚀 Funcionalidades

### Dashboard Streamlit Executivo
- **Análises Financeiras**: Faturamento, lucro, margem e ticket médio
- **Análise de Cohort**: Retenção de clientes por safra
- **Análise de Produtos**: Top produtos e análise de cross-selling
- **Segmentação RFM**: Classificação de clientes (VIP, Leal, Novo, Comum, Churn)
- **Análises Geográficas**: Distribuição por estado e região
- **Forecasting**: Projeções de faturamento baseadas em tendências
- **Detecção de Anomalias**: Identificação de fraudes e erros usando IA (Isolation Forest)

### Gerador de Dados
- Geração de dados realistas de e-commerce usando Faker e Factory Boy
- Bulk create otimizado para performance
- Integridade temporal (clientes não podem fazer pedidos antes de seu cadastro)
- Simulação de churn baseada em tempo de vida do cliente
- Mapeamento correto de região/estado brasileiros

### Infraestrutura
- Docker Compose com PostgreSQL, Django e Superset
- CI/CD com GitHub Actions
- Credenciais padronizadas via variáveis de ambiente
- Queries SQL prontas para análise no Superset

## 📋 Pré-requisitos

- Python 3.12+
- Docker e Docker Compose (opcional, para ambiente completo)
- PostgreSQL 15+

## 🔧 Instalação

### Usando Docker (Recomendado)

```bash
# Clone o repositório
git clone https://github.com/Fryansb/ecommerce-data-generator.git
cd ecommerce-data-generator

# Inicie os serviços
docker-compose up -d

# Acesse:
# - Django Admin: http://localhost:8000/admin
# - Superset: http://localhost:8088
```

### Instalação Local

```bash
# Clone o repositório
git clone https://github.com/Fryansb/ecommerce-data-generator.git
cd ecommerce-data-generator

# Crie e ative um ambiente virtual
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Configure o banco de dados
export DB_NAME=thelook_db
export DB_USER=thelook_user
export DB_PASS=thelook_pass
export DB_HOST=localhost
export DB_PORT=5432

# Execute as migrações
python manage.py migrate

# Gere dados de exemplo
python manage.py simulate_data --years 2

# Inicie o servidor Django
python manage.py runserver
```

## 📊 Dashboard Streamlit

Para iniciar o dashboard Streamlit:

```bash
# Configure as variáveis de ambiente
export POSTGRES_USER=thelook_user
export POSTGRES_PASSWORD=thelook_pass
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=thelook_db

# Inicie o Streamlit
streamlit run streamlit_app.py
```

O dashboard estará disponível em: http://localhost:8501

## 🧪 Testes

```bash
# Execute todos os testes
pytest --ds=config.settings --maxfail=1 --disable-warnings -v

# Execute testes específicos
pytest tests/test_models.py -v
pytest tests/test_factories.py -v
pytest tests/test_simulate_data.py -v
```

## 📁 Estrutura do Projeto

```
.
├── config/                 # Configurações Django
│   └── settings.py        # Settings com suporte a env vars
├── core/                  # App principal Django
│   ├── models.py         # Modelos (Customer, Product, Order, OrderItem)
│   └── management/
│       └── commands/
│           └── simulate_data.py  # Gerador de dados com bulk create
├── tests/                # Testes unitários
├── streamlit_app.py      # Dashboard executivo Streamlit
├── superset_query.sql    # Query para análise no Superset
├── docker-compose.yml    # Orquestração de serviços
├── requirements.txt      # Dependências Python
└── .gitignore           # Arquivos ignorados (venv, .pyc, etc.)
```

## 🔐 Variáveis de Ambiente

| Variável | Descrição | Default |
|----------|-----------|---------|
| `DB_NAME` | Nome do banco de dados | `thelook_db` |
| `DB_USER` | Usuário do PostgreSQL | `thelook_user` |
| `DB_PASS` | Senha do PostgreSQL | `thelook_pass` |
| `DB_HOST` | Host do PostgreSQL | `localhost` |
| `DB_PORT` | Porta do PostgreSQL | `5432` |
| `POSTGRES_USER` | Usuário PostgreSQL (Streamlit) | `thelook_user` |
| `POSTGRES_PASSWORD` | Senha PostgreSQL (Streamlit) | `thelook_pass` |
| `POSTGRES_HOST` | Host PostgreSQL (Streamlit) | `localhost` |
| `POSTGRES_PORT` | Porta PostgreSQL (Streamlit) | `5432` |
| `POSTGRES_DB` | Database PostgreSQL (Streamlit) | `thelook_db` |

## 📈 Análise no Superset

1. Acesse o Superset em http://localhost:8088
2. Configure a conexão com o PostgreSQL
3. Use a query em `superset_query.sql` para criar datasets
4. Crie dashboards com as dimensões disponíveis

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT.

## 👥 Autores

- **Fryansb** - [GitHub](https://github.com/Fryansb)

## 🙏 Agradecimentos

- Faker-br para geração de dados brasileiros
- Streamlit para o dashboard interativo
- Plotly para visualizações avançadas
- Scikit-learn para detecção de anomalias
