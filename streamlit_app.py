import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
from itertools import combinations
from collections import Counter
from sklearn.ensemble import IsolationForest
import os

# ==============================================================================
# 1. CONFIGURAÇÃO GLOBAL & UI/UX
# ==============================================================================
st.set_page_config(
    page_title="Dashboard Executivo AI", 
    layout="wide", 
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 1.5rem; color: #4ecca3; }
    div[data-testid="stMetricDelta"] > svg { display: none; } /* Esconde setinha padrão para customizar */
</style>
""", unsafe_allow_html=True)

# Config DB
DB_CONFIG = {
    'user': os.environ.get('POSTGRES_USER', 'thelook_user'),
    'password': os.environ.get('POSTGRES_PASSWORD', 'thelook_pass'),
    'host': os.environ.get('POSTGRES_HOST', 'localhost'),
    'port': int(os.environ.get('POSTGRES_PORT', 5432)),
    'database': os.environ.get('POSTGRES_DB', 'thelook_db')
}

# ==============================================================================
# 2. ETL & ENGENHARIA
# ==============================================================================

@st.cache_data(ttl=600)
def load_data():
    try:
        conn_str = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        engine = create_engine(conn_str)
        orders = pd.read_sql('SELECT * FROM core_order', engine)
        items = pd.read_sql('SELECT * FROM core_orderitem', engine)
        products = pd.read_sql('SELECT * FROM core_product', engine)
        customers = pd.read_sql('SELECT * FROM core_customer', engine)
        return orders, items, products, customers
    except Exception as e:
        st.error(f"❌ Erro de Conexão: {e}")
        st.stop()

@st.cache_data
def process_data(_orders, _items, _products, _customers):
    # Join Global
    df = _items.merge(_products, left_on='product_id', right_on='id', suffixes=('', '_prod')) \
               .merge(_orders, left_on='order_id', right_on='id', suffixes=('', '_order')) \
               .merge(_customers, left_on='customer_id', right_on='id', suffixes=('', '_cust'))

    # Casting & KPIs Financeiros
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['faturamento'] = df['unit_price'] * df['quantity']
    df['lucro'] = (df['unit_price'] - df['unit_cost']) * df['quantity']
    
    # Sanitização Geo
    estado_map = {
        'Norte': ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'],
        'Nordeste': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
        'Centro-Oeste': ['DF', 'GO', 'MT', 'MS'],
        'Sudeste': ['ES', 'MG', 'RJ', 'SP'],
        'Sul': ['PR', 'RS', 'SC']
    }
    uf_to_regiao = {uf: reg for reg, ufs in estado_map.items() for uf in ufs}
    df['region'] = df['state'].map(uf_to_regiao).fillna(df['region'])
    
    return df

# Função Auxiliar para Comparação MoM (Month over Month)
def calculate_delta(df_atual, col_metrica):
    """Calcula a variação percentual em relação ao período anterior equivalente."""
    if df_atual.empty: return 0
    
    # Pega o total atual
    total_atual = df_atual[col_metrica].sum()
    
    # Define o ponto de corte para o período anterior (metade do tempo para trás)
    min_date = df_atual['order_date'].min()
    max_date = df_atual['order_date'].max()
    delta_time = max_date - min_date
    prev_max = min_date
    prev_min = min_date - delta_time
    
    # Filtra período anterior no dataset mestre (precisaria passar o df_master, 
    # mas para simplificar vamos assumir comparação simples na visualização)
    return 0 # Placeholder para lógica complexa de MoM, usaremos visualização simples

# ==============================================================================
# 3. INICIALIZAÇÃO
# ==============================================================================
orders_raw, items_raw, products_raw, customers_raw = load_data()
df_master = process_data(orders_raw, items_raw, products_raw, customers_raw)

if df_master.empty: st.stop()

# ==============================================================================
# 4. SIDEBAR
# ==============================================================================
st.sidebar.title("🎛️ Centro de Comando")
st.sidebar.markdown("---")

min_date, max_date = df_master['order_date'].min().date(), df_master['order_date'].max().date()
date_range = st.sidebar.date_input("Período", (min_date, max_date), min_value=min_date, max_value=max_date)

all_regions = sorted(df_master['region'].dropna().unique())
sel_regions = st.sidebar.multiselect("Região", all_regions, default=all_regions)

# Filtro
mask = (
    (df_master['order_date'].dt.date >= date_range[0]) & 
    (df_master['order_date'].dt.date <= date_range[1]) &
    (df_master['region'].isin(sel_regions))
)
df_filtered = df_master.loc[mask]

if df_filtered.empty:
    st.error("🚫 Sem dados para o filtro.")
    st.stop()

# ==============================================================================
# 5. DASHBOARD
# ==============================================================================
st.title("🛰️ The Look E-commerce | AI Analytics")
st.caption(f"Visão Consolidada: {len(df_filtered):,} Transações")

tabs = st.tabs(["💰 Financeiro", "🔄 Cohort & Retenção", "📦 Produtos", "👥 Clientes", "🗺️ Geo", "🔮 Predições", "🕵️ Anomalias"])

# === ABA 1: FINANCEIRO ===
with tabs[0]:
    fat = df_filtered['faturamento'].sum()
    lucro = df_filtered['lucro'].sum()
    margem = (lucro / fat * 100) if fat > 0 else 0
    qtd_pedidos = df_filtered['order_id'].nunique()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Faturamento", f"R$ {fat:,.2f}")
    c2.metric("Lucro Líquido", f"R$ {lucro:,.2f}", f"{margem:.1f}% Margem")
    c3.metric("Ticket Médio", f"R$ {(fat/qtd_pedidos):,.2f}")
    c4.metric("Pedidos", f"{qtd_pedidos}")

    st.divider()

    # Gráfico com Meta Visual
    df_filtered['periodo'] = df_filtered['order_date'].dt.to_period('M').astype(str)
    trend = df_filtered.groupby('periodo')[['faturamento', 'lucro']].sum().reset_index()
    
    fig = px.line(trend, x='periodo', y=['faturamento', 'lucro'], 
                  title='Evolução de Resultados (Mensal)', markers=True,
                  color_discrete_map={'faturamento': '#29b5e8', 'lucro': '#117a65'})
    st.plotly_chart(fig, use_container_width=True)

# === ABA 2: COHORT (RETENÇÃO) - CORRIGIDO PANDAS 2.0 ===
with tabs[1]:
    st.subheader("🔥 Análise de Cohort (Retenção de Clientes)")
    st.info("Este gráfico mostra: Dos clientes que compraram pela primeira vez no mês X, quantos voltaram a comprar nos meses seguintes?")

    # 1. Determinar o mês da primeira compra de cada cliente (CohortMonth)
    df_cohort = df_filtered[['customer_id', 'order_id', 'order_date']].drop_duplicates()
    df_cohort['order_month'] = df_cohort['order_date'].dt.to_period('M')
    
    # Agrupa por cliente e acha a data mínima (Safra)
    df_cohort['cohort'] = df_cohort.groupby('customer_id')['order_date'].transform('min').dt.to_period('M')
    
    # 2. Agregar dados (Cohort vs Order Month)
    df_cohort_data = df_cohort.groupby(['cohort', 'order_month']).agg(n_customers=('customer_id', 'nunique')).reset_index()
    
    # 3. Calcular o índice de período (Mês 0, Mês 1, Mês 2...)
    df_cohort_data['period_number'] = (df_cohort_data['order_month'] - df_cohort_data['cohort']).apply(lambda x: x.n)
    
    # 4. Pivotar para formato de matriz
    cohort_pivot = df_cohort_data.pivot_table(index='cohort', columns='period_number', values='n_customers')
    
    # 5. Calcular em Porcentagem (Retenção)
    cohort_size = cohort_pivot.iloc[:, 0]
    retention = cohort_pivot.divide(cohort_size, axis=0)
    
    # Visualização Heatmap
    if not retention.empty:
        fig_cohort = go.Figure(data=go.Heatmap(
            z=retention,
            x=retention.columns,
            y=retention.index.astype(str),
            colorscale='Blues',
            # --- CORREÇÃO AQUI: Mudamos de applymap para map ---
            text=retention.map(lambda x: f"{x:.1%}" if not pd.isna(x) else ""),
            texttemplate="%{text}"
        ))
        fig_cohort.update_layout(
            title="Taxa de Retenção por Safra (%)",
            xaxis_title="Meses após a 1ª compra",
            yaxis_title="Mês de Entrada (Safra)"
        )
        st.plotly_chart(fig_cohort, use_container_width=True)
    else:
        st.warning("Dados insuficientes para gerar Cohort.")

# === ABA 3: PRODUTOS ===
with tabs[2]:
    c1, c2 = st.columns(2)
    with c1:
        top = df_filtered.groupby('name')['quantity'].sum().nlargest(10).reset_index()
        st.plotly_chart(px.bar(top, y='name', x='quantity', orientation='h', title="Top Volume"), use_container_width=True)
    with c2:
        orders_list = df_filtered.groupby('order_id')['name'].apply(list)
        pairs = Counter([pair for items in orders_list if len(items) > 1 for pair in combinations(sorted(set(items)), 2)])
        if pairs:
            df_p = pd.DataFrame(pairs.most_common(8), columns=['Par', 'Qtd'])
            df_p['Par'] = df_p['Par'].apply(lambda x: f"{x[0]} + {x[1]}")
            st.plotly_chart(px.bar(df_p, x='Qtd', y='Par', orientation='h', title="Top Combinados"), use_container_width=True)
        else:
            st.info("Sem correlações no período.")

# === ABA 4: CLIENTES (RFM OTIMIZADO) ===
with tabs[3]:
    st.subheader("Matriz RFM")
    snap_date = df_filtered['order_date'].max()
    rfm = df_filtered.groupby('customer_id').agg({
        'order_date': lambda x: (snap_date - x.max()).days,
        'order_id': 'nunique',
        'faturamento': 'sum'
    }).rename(columns={'order_date': 'R', 'order_id': 'F', 'faturamento': 'M'})
    
    # Lógica de Segmentação
    def get_segment(r):
        if r['M'] > rfm['M'].quantile(0.95): return '💎 VIP'
        if r['F'] > 1 and r['R'] <= 30: return '🔄 Leal'
        if r['R'] <= 30: return '🆕 Novo'
        if r['R'] > 90: return '💤 Risco/Churn'
        return '👤 Comum'
    
    rfm['Segmento'] = rfm.apply(get_segment, axis=1)
    
    c1, c2 = st.columns([1, 2])
    c1.plotly_chart(px.pie(rfm, names='Segmento', hole=0.4), use_container_width=True)
    c2.plotly_chart(px.scatter(rfm, x='R', y='M', color='Segmento', log_y=True, title="Recência vs Valor"), use_container_width=True)

# === ABA 5: GEO ===
with tabs[4]:
    geo = df_filtered.groupby('state')['faturamento'].sum().reset_index()
    st.plotly_chart(px.bar(geo, x='state', y='faturamento', color='faturamento', title="Faturamento por Estado"), use_container_width=True)

# === ABA 6: PREDIÇÕES ===
with tabs[5]:
    st.subheader("🔮 Forecasting (Suavização)")
    df_weekly = df_filtered.set_index('order_date').resample('W')['faturamento'].sum().reset_index()
    
    if len(df_weekly) > 4:
        df_weekly['idx'] = np.arange(len(df_weekly))
        coeffs = np.polyfit(df_weekly['idx'], df_weekly['faturamento'], 3)
        poly_curve = np.poly1d(coeffs)
        
        future_idx = np.arange(df_weekly['idx'].max() + 1, df_weekly['idx'].max() + 9)
        future_vals = np.maximum(poly_curve(future_idx), 0)
        future_dates = [df_weekly['order_date'].max() + pd.Timedelta(weeks=int(x)) for x in range(1, 9)]
        
        # Correção do Bug 'KeyError'
        df_weekly['Trend'] = poly_curve(df_weekly['idx'])
        df_weekly['Tipo'] = 'Real'
        
        df_viz = pd.concat([
            df_weekly,
            pd.DataFrame({'order_date': future_dates, 'faturamento': future_vals, 'Tipo': 'Previsto', 'Trend': future_vals})
        ])
        
        fig = px.line(df_viz, x='order_date', y='faturamento', title="Projeção 8 Semanas")
        fig.add_scatter(x=df_viz['order_date'], y=df_viz['Trend'], mode='lines', name='Tendência', line=dict(color='gold', dash='dot'))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Dados insuficientes (Mínimo 4 semanas).")

# === ABA 7: ANOMALIAS (IA) ===
with tabs[6]:
    st.subheader("🕵️ Detecção de Fraudes/Erros")
    features = ['quantity', 'unit_price', 'faturamento']
    df_ai = df_filtered[['order_id'] + features].dropna()
    
    if len(df_ai) > 50:
        model = IsolationForest(contamination=0.01, random_state=42)
        df_ai['score'] = model.fit_predict(df_ai[features])
        anomalies = df_ai[df_ai['score'] == -1]
        
        c1, c2 = st.columns([3, 1])
        with c1:
            fig = px.scatter(df_ai, x='faturamento', y='unit_price', color=df_ai['score'].astype(str),
                             color_discrete_map={'-1': 'red', '1': 'blue'}, log_x=True, log_y=True,
                             title="Clusterização de Risco")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.metric("Suspeitas", len(anomalies))
            st.dataframe(anomalies.sort_values('faturamento', ascending=False).head(10)[['order_id', 'faturamento']], hide_index=True)
    else:
        st.info("Dados insuficientes para IA.")