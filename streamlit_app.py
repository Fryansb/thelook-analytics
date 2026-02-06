from typing import Optional, Tuple
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from itertools import combinations
from collections import Counter
from sklearn.ensemble import IsolationForest

from core.data_utils import RedisClient, DataLoader
from core.simulation_constants import UF_TO_REGION_MAP

st.set_page_config(
    page_title="Dashboard Executivo AI", layout="wide", initial_sidebar_state="expanded"
)

st.markdown(
    """
<style>
    [data-testid="stMetricValue"] { font-size: 1.5rem; color: #4ecca3; }
    div[data-testid="stMetricDelta"] > svg { display: none; }
</style>
""",
    unsafe_allow_html=True,
)


def get_faturamento_redis(data: Optional[object] = None) -> Optional[float]:
    return RedisClient.get_metric("faturamento", data, float)


@st.cache_data(ttl=300)
def _get_product_lifecycle_map() -> dict:
    engine = DataLoader.get_engine()
    products_db = pd.read_sql("SELECT name, lifecycle FROM core_product", engine)
    return dict(zip(products_db["name"], products_db["lifecycle"]))


def get_top_produtos_redis(limit: int = 100) -> list:
    produto_nomes = RedisClient.get_top_products(limit)
    if not produto_nomes:
        return []

    try:
        lifecycle_map = _get_product_lifecycle_map()
        return [
            (nome, score, lifecycle_map.get(nome, "Desconhecido"))
            for nome, score in produto_nomes
        ]
    except Exception:
        return [(nome, score, "N/A") for nome, score in produto_nomes]


def get_vendas_por_regiao_redis() -> dict:
    return RedisClient.get_regional_sales()


def get_pedidos_count_redis(data: Optional[object] = None) -> Optional[int]:
    return RedisClient.get_metric("pedidos_count", data, int)


def get_clientes_ativos_redis(data: Optional[object] = None) -> Optional[int]:
    return RedisClient.get_metric("clientes_ativos", data, int)


@st.cache_data(ttl=300)
def load_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    try:
        return DataLoader.load_tables()
    except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        st.stop()


def process_data(
    _orders: pd.DataFrame,
    _items: pd.DataFrame,
    _products: pd.DataFrame,
    _customers: pd.DataFrame,
) -> pd.DataFrame:
    df = (
        _items.merge(
            _products,
            left_on="product_id",
            right_on="id",
            how="inner",
            suffixes=("", "_prod"),
        )
        .merge(
            _orders,
            left_on="order_id",
            right_on="id",
            how="inner",
            suffixes=("", "_order"),
        )
        .merge(
            _customers,
            left_on="customer_id",
            right_on="id",
            how="inner",
            suffixes=("", "_cust"),
        )
    )

    df["order_date"] = pd.to_datetime(df["order_date"])
    df["faturamento"] = df["unit_price"] * df["quantity"]
    df["lucro"] = (df["unit_price"] - df["unit_cost"]) * df["quantity"]
    df["region"] = df["state"].map(UF_TO_REGION_MAP).fillna(df["region"])

    return df


orders_raw, items_raw, products_raw, customers_raw = load_data()
df_master = process_data(orders_raw, items_raw, products_raw, customers_raw)

if df_master.empty:
    st.stop()

st.sidebar.title("Centro de Comando")
st.sidebar.markdown("---")

if st.sidebar.button("Atualizar dados"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

min_date, max_date = (
    df_master["order_date"].min().date(),
    df_master["order_date"].max().date(),
)
date_range = st.sidebar.date_input(
    "Período", (min_date, max_date), min_value=min_date, max_value=max_date
)

all_regions = sorted(df_master["region"].dropna().unique())
sel_regions = st.sidebar.multiselect("Região", all_regions, default=all_regions)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = (
        date_range if not isinstance(date_range, tuple) else min_date
    )

mask = (
    (df_master["order_date"].dt.date >= start_date)
    & (df_master["order_date"].dt.date <= end_date)
    & ((df_master["region"].isin(sel_regions)) | (df_master["region"].isna()))
)
df_filtered = df_master.loc[mask]

if df_filtered.empty:
    st.error("Sem dados para o filtro.")
    st.stop()

st.title("The Look E-commerce | AI Analytics")
st.caption(f"Visão Consolidada: {len(df_filtered):,} Transações")

hoje = pd.Timestamp.now().date()
hoje_str = hoje.strftime("%d/%m/%Y")
st.markdown(f"### Métricas em Tempo Real (Redis)")
st.caption(f"Período: Dia {hoje_str} das 00:00 às 23:59 | Todas as regiões")
redis_c1, redis_c2, redis_c3, redis_c4, redis_c5 = st.columns(5)

use_redis = True

redis_faturamento_hoje = get_faturamento_redis()
redis_pedidos_hoje = get_pedidos_count_redis()
redis_clientes_ativos = get_clientes_ativos_redis()
redis_label_suffix = "Hoje"

with redis_c1:
    if redis_faturamento_hoje is not None:
        st.metric(
            f"Faturamento {redis_label_suffix}", f"R$ {redis_faturamento_hoje:,.2f}"
        )
    else:
        st.metric(f"Faturamento {redis_label_suffix}", "N/A")

with redis_c2:
    if redis_pedidos_hoje is not None:
        st.metric(f"Pedidos {redis_label_suffix}", f"{redis_pedidos_hoje:,}")
    else:
        st.metric(f"Pedidos {redis_label_suffix}", "N/A")

with redis_c3:
    if redis_clientes_ativos is not None:
        st.metric(f"Clientes Ativos {redis_label_suffix}", f"{redis_clientes_ativos:,}")
    else:
        st.metric(f"Clientes Ativos {redis_label_suffix}", "N/A")

with redis_c4:
    if redis_faturamento_hoje and redis_pedidos_hoje and redis_pedidos_hoje > 0:
        ticket = redis_faturamento_hoje / redis_pedidos_hoje
        st.metric(f"Ticket Médio {redis_label_suffix}", f"R$ {ticket:,.2f}")
    else:
        st.metric(f"Ticket Médio {redis_label_suffix}", "N/A")

with redis_c5:
    top_produtos = get_top_produtos_redis()
    if top_produtos:
        st.metric("Top Produto", top_produtos[0][0][:20] + "...")
    else:
        st.metric("Top Produto", "N/A")

st.divider()

tabs = st.tabs(
    [
        "Financeiro",
        "Cohort & Retenção",
        "Produtos",
        "Clientes",
        "Geo",
        "Predições",
        "Anomalias",
    ]
)

with tabs[0]:
    st.caption(
        "Análise consolidada de faturamento, lucro e margens do período selecionado. "
        "Valores calculados a partir de pedidos concluídos."
    )
    fat = df_filtered["faturamento"].sum()
    lucro = df_filtered["lucro"].sum()
    margem = (lucro / fat * 100) if fat > 0 else 0
    qtd_pedidos = df_filtered["order_id"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Faturamento", f"R$ {fat:,.2f}")
    c2.metric("Lucro Líquido", f"R$ {lucro:,.2f}", f"{margem:.1f}% Margem")
    c3.metric("Ticket Médio", f"R$ {(fat/qtd_pedidos):,.2f}")
    c4.metric("Pedidos", f"{qtd_pedidos}")

    st.divider()

    df_filtered["periodo"] = df_filtered["order_date"].dt.to_period("M").astype(str)
    trend = df_filtered.groupby("periodo")[["faturamento", "lucro"]].sum().reset_index()

    fig = px.line(
        trend,
        x="periodo",
        y=["faturamento", "lucro"],
        title="Evolução de Resultados (Mensal)",
        markers=True,
        color_discrete_map={"faturamento": "#29b5e8", "lucro": "#117a65"},
    )
    st.plotly_chart(fig, width="stretch")

with tabs[1]:
    st.subheader("Análise de Cohort (Retenção de Clientes)")
    st.caption(
        "Métrica de retenção: percentual de clientes de cada safra (mês de primeira compra) "
        "que retornaram nos meses subsequentes. Eixo Y = mês de entrada, "
        "Eixo X = meses após primeira compra."
    )

    df_cohort = df_filtered[["customer_id", "order_id", "order_date"]].drop_duplicates()
    df_cohort["order_month"] = df_cohort["order_date"].dt.to_period("M")
    df_cohort["cohort"] = (
        df_cohort.groupby("customer_id")["order_date"]
        .transform("min")
        .dt.to_period("M")
    )

    df_cohort_data = (
        df_cohort.groupby(["cohort", "order_month"])
        .agg(n_customers=("customer_id", "nunique"))
        .reset_index()
    )
    df_cohort_data["period_number"] = (
        df_cohort_data["order_month"] - df_cohort_data["cohort"]
    ).apply(lambda x: x.n)

    cohort_pivot = df_cohort_data.pivot_table(
        index="cohort", columns="period_number", values="n_customers"
    )
    cohort_size = cohort_pivot.iloc[:, 0]
    retention = cohort_pivot.divide(cohort_size, axis=0)

    # Visualização Heatmap
    if not retention.empty:
        # Formatar como percentual
        retention_text = retention.map(lambda x: f"{x:.0%}" if not pd.isna(x) else "")

        fig_cohort = go.Figure(
            data=go.Heatmap(
                z=retention,
                x=retention.columns,
                y=retention.index.astype(str),
                colorscale="Blues",
                text=retention_text.values,
                texttemplate="%{text}",
                textfont={"size": 10},
                colorbar=dict(title="Retenção"),
            )
        )
        fig_cohort.update_layout(
            title="Taxa de Retenção por Safra (%) - Dos clientes que compraram no mês X, quantos retornaram?",
            xaxis_title="Meses após a 1ª compra",
            yaxis_title="Mês de Entrada (Safra)",
            height=500,
            font=dict(size=11),
            hovermode="closest",
        )
        st.plotly_chart(fig_cohort, width="stretch")
    else:
        st.warning("Dados insuficientes para gerar Cohort.")

with tabs[2]:
    st.markdown("#### Ciclo de Vida dos Produtos")
    st.caption(
        "Classificação de produtos por estágio: Viral (alta demanda crescente), "
        "Estável (vendas consistentes), Obsoleto (declínio ou baixo volume). "
        "Motivos calculados com base em volume de vendas e faturamento."
    )

    try:
        engine = DataLoader.get_engine()
        products_query = (
            "SELECT id, name, lifecycle, category FROM core_product ORDER BY name"
        )
        df_products_lifecycle = pd.read_sql(products_query, engine)

        col1, col2, col3 = st.columns(3)

        with col1:
            viral_count = len(
                df_products_lifecycle[df_products_lifecycle["lifecycle"] == "Viral"]
            )
            st.metric(
                "Viral",
                viral_count,
                f"{viral_count/len(df_products_lifecycle)*100:.1f}%",
            )

        with col2:
            stable_count = len(
                df_products_lifecycle[df_products_lifecycle["lifecycle"] == "Stable"]
            )
            st.metric(
                "Estável",
                stable_count,
                f"{stable_count/len(df_products_lifecycle)*100:.1f}%",
            )

        with col3:
            obsolete_count = len(
                df_products_lifecycle[df_products_lifecycle["lifecycle"] == "Obsolete"]
            )
            st.metric(
                "Obsoleto",
                obsolete_count,
                f"{obsolete_count/len(df_products_lifecycle)*100:.1f}%",
            )

        st.divider()
        lifecycle_type = st.selectbox(
            "Filtrar por Ciclo de Vida", ["Viral", "Stable", "Obsolete", "Todos"]
        )

        if lifecycle_type == "Todos":
            df_show = df_products_lifecycle.copy()
        else:
            df_show = df_products_lifecycle[
                df_products_lifecycle["lifecycle"] == lifecycle_type
            ].copy()

        vendas_por_produto = (
            df_master.groupby("name")
            .agg({"quantity": "sum", "unit_price": ["mean", "sum"]})
            .reset_index()
        )
        vendas_por_produto.columns = [
            "product_name",
            "quantidade_total",
            "preco_medio",
            "faturamento_total",
        ]

        df_show = df_show.merge(
            vendas_por_produto, left_on="name", right_on="product_name", how="left"
        )
        df_show = df_show.copy()
        df_show["quantidade_total"] = df_show["quantidade_total"].fillna(0).astype(int)
        df_show["faturamento_total"] = df_show["faturamento_total"].fillna(0)

        # Calcular motivos
        def get_motivo(row):
            lifecycle = row["lifecycle"]
            qtd = row["quantidade_total"]
            fatur = row["faturamento_total"]

            if lifecycle == "Viral":
                if qtd > 1000:
                    return f"Alto volume: {int(qtd):,} unidades"
                elif fatur > 50000:
                    return f"Alto faturamento: R$ {fatur:,.0f}"
                else:
                    return "Tendência crescente"
            elif lifecycle == "Stable":
                if qtd > 500:
                    return f"Volume consistente: {int(qtd):,} unidades"
                elif fatur > 20000:
                    return f"Faturamento estável: R$ {fatur:,.0f}"
                else:
                    return "Desempenho previsível"
            else:  # Obsolete
                if qtd < 100:
                    return f"Baixo volume: {int(qtd):,} unidades"
                else:
                    return f"Vendas em declínio: {int(qtd):,} unidades"

        df_show["Motivo"] = df_show.apply(get_motivo, axis=1)

        st.dataframe(
            df_show[["id", "name", "category", "lifecycle", "Motivo"]].reset_index(
                drop=True
            ),
            width="stretch",
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "name": "Produto",
                "category": "Categoria",
                "lifecycle": "Ciclo",
                "Motivo": "Por que?",
            },
        )
    except Exception as e:
        st.error(f"Erro ao carregar produtos: {e}")

    st.divider()

    st.markdown("#### Top Produtos (Redis Cache)")
    top_n = st.slider(
        "Quantos top produtos deseja visualizar?",
        min_value=5,
        max_value=100,
        value=10,
        step=5,
    )

    top_produtos_redis = get_top_produtos_redis(limit=top_n)
    if top_produtos_redis:
        df_redis_produtos = pd.DataFrame(
            top_produtos_redis, columns=["Produto", "Quantidade", "Ciclo de Vida"]
        )
        st.dataframe(df_redis_produtos, width="stretch")
    else:
        st.info("Redis não disponível")

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        top = df_filtered.groupby("name")["quantity"].sum().nlargest(10).reset_index()
        st.plotly_chart(
            px.bar(top, y="name", x="quantity", orientation="h", title="Top Volume"),
            width="stretch",
        )
    with c2:
        orders_list = df_filtered.groupby("order_id")["name"].apply(list)
        pairs = Counter(
            [
                pair
                for items in orders_list
                if len(items) > 1
                for pair in combinations(sorted(set(items)), 2)
            ]
        )
        if pairs:
            df_p = pd.DataFrame(pairs.most_common(8), columns=["Par", "Qtd"])
            df_p["Par"] = df_p["Par"].apply(lambda x: f"{x[0]} + {x[1]}")
            st.plotly_chart(
                px.bar(df_p, x="Qtd", y="Par", orientation="h", title="Top Combinados"),
                width="stretch",
            )
        else:
            st.info("Sem correlações no período.")

with tabs[3]:
    st.subheader("Matriz RFM")
    st.caption(
        "Segmentação RFM: Recência (dias desde última compra), "
        "Frequência (número de pedidos), Monetary (valor total). "
        "VIP = top 5% faturamento, Leal = múltiplas compras recentes, "
        "Novo = primeira compra <30 dias, Risco/Churn = >90 dias inativo."
    )
    snap_date = df_filtered["order_date"].max()
    rfm = (
        df_filtered.groupby("customer_id")
        .agg(
            {
                "order_date": lambda x: (snap_date - x.max()).days,
                "order_id": "nunique",
                "faturamento": "sum",
            }
        )
        .rename(columns={"order_date": "R", "order_id": "F", "faturamento": "M"})
    )

    def get_segment(r):
        if r["M"] > rfm["M"].quantile(0.95):
            return "VIP"
        if r["F"] > 1 and r["R"] <= 30:
            return "Leal"
        if r["R"] <= 30:
            return "Novo"
        if r["R"] > 90:
            return "Risco/Churn"
        return "Comum"

    rfm["Segmento"] = rfm.apply(get_segment, axis=1)

    c1, c2 = st.columns([1, 2])
    c1.plotly_chart(px.pie(rfm, names="Segmento", hole=0.4), width="stretch")
    c2.plotly_chart(
        px.scatter(
            rfm, x="R", y="M", color="Segmento", log_y=True, title="Recência vs Valor"
        ),
        width="stretch",
    )

with tabs[4]:
    st.markdown("#### Análise Geográfica")
    st.caption(
        "Distribuição de vendas por região e estado. "
        "Valores agregados do período selecionado nos filtros. "
        "Hover no mapa para detalhes por estado."
    )

    vendas_regiao = (
        df_filtered.groupby("region")["faturamento"].sum().sort_values(ascending=False)
    )
    if not vendas_regiao.empty:
        geo_cols = st.columns(len(vendas_regiao))
        for idx, (regiao, valor) in enumerate(vendas_regiao.items()):
            with geo_cols[idx]:
                st.metric(regiao, f"R$ {valor:,.0f}")
    else:
        st.info("Sem dados no período")

    st.divider()

    geo_state = (
        df_filtered.groupby("state")
        .agg({"faturamento": "sum", "order_id": "nunique", "customer_id": "nunique"})
        .reset_index()
    )
    geo_state.columns = ["UF", "Faturamento", "Pedidos", "Clientes"]
    geo_state["Ticket Médio"] = geo_state["Faturamento"] / geo_state["Pedidos"]

    col1, col2 = st.columns([2, 1])

    with col1:
        fig_bar = px.bar(
            geo_state.sort_values("Faturamento", ascending=True).tail(15),
            y="UF",
            x="Faturamento",
            orientation="h",
            title="Top 15 Estados por Faturamento",
            color="Faturamento",
            color_continuous_scale="Viridis",
            hover_data={"Faturamento": ":,.0f", "Pedidos": ":,", "Clientes": ":,"},
        )
        st.plotly_chart(fig_bar, width="stretch")

    with col2:
        st.dataframe(
            geo_state.sort_values("Faturamento", ascending=False),
            width="stretch",
            hide_index=True,
            column_config={
                "UF": st.column_config.TextColumn("Estado", width="small"),
                "Faturamento": st.column_config.NumberColumn(
                    "Faturamento", format="R$ %.0f"
                ),
                "Pedidos": st.column_config.NumberColumn("Pedidos", format="%d"),
                "Clientes": st.column_config.NumberColumn("Clientes", format="%d"),
                "Ticket Médio": st.column_config.NumberColumn(
                    "Ticket Médio", format="R$ %.2f"
                ),
            },
        )

with tabs[5]:
    st.subheader("Forecasting (Suavização)")
    st.caption(
        "Projeção de faturamento para as próximas 8 semanas usando regressão polinomial de grau 3. "
        "Linha azul = dados reais, linha dourada pontilhada = tendência, "
        "extensão da tendência = previsão."
    )
    df_weekly = (
        df_filtered.set_index("order_date")
        .resample("W")["faturamento"]
        .sum()
        .reset_index()
    )

    if len(df_weekly) > 4:
        df_weekly["idx"] = np.arange(len(df_weekly))
        coeffs = np.polyfit(df_weekly["idx"], df_weekly["faturamento"], 3)
        poly_curve = np.poly1d(coeffs)

        future_idx = np.arange(df_weekly["idx"].max() + 1, df_weekly["idx"].max() + 9)
        future_vals = np.maximum(poly_curve(future_idx), 0)
        future_dates = [
            df_weekly["order_date"].max() + pd.Timedelta(weeks=int(x))
            for x in range(1, 9)
        ]

        df_weekly["Trend"] = poly_curve(df_weekly["idx"])
        df_weekly["Tipo"] = "Real"

        df_viz = pd.concat(
            [
                df_weekly,
                pd.DataFrame(
                    {
                        "order_date": future_dates,
                        "faturamento": future_vals,
                        "Tipo": "Previsto",
                        "Trend": future_vals,
                    }
                ),
            ]
        )

        fig = px.line(
            df_viz, x="order_date", y="faturamento", title="Projeção 8 Semanas"
        )
        fig.add_scatter(
            x=df_viz["order_date"],
            y=df_viz["Trend"],
            mode="lines",
            name="Tendência",
            line=dict(color="gold", dash="dot"),
        )
        st.plotly_chart(fig, width="stretch")
    else:
        st.warning("Dados insuficientes (Mínimo 4 semanas).")

with tabs[6]:
    st.subheader("Detecção de Fraudes/Erros")
    st.caption(
        "Algoritmo Isolation Forest identifica padrões anômalos: compras em excesso, preços fora do padrão ou valores totais suspeitos. Pontos vermelhos = anomalias detectadas (1% contaminação esperada)."
    )
    features = ["quantity", "unit_price", "faturamento"]
    df_ai = df_filtered[
        ["order_id", "customer_id", "quantity", "unit_price", "faturamento"]
        + (["product_id"] if "product_id" in df_filtered.columns else [])
    ].dropna()

    if len(df_ai) > 50:
        model = IsolationForest(contamination=0.01, random_state=42)
        df_ai["anomaly_score"] = model.fit_predict(df_ai[features])
        anomalies = df_ai[df_ai["anomaly_score"] == -1].copy()

        q95_qty = df_ai["quantity"].quantile(0.95)
        q95_price = df_ai["unit_price"].quantile(0.95)
        q95_faturamento = df_ai["faturamento"].quantile(0.95)

        def categorize_fraud(row, q_qty, q_price, q_fat):
            if row["quantity"] > q_qty:
                return (
                    "Compra em Excesso",
                    f"Quantidade anormal: {int(row['quantity'])} unidades (limite: {int(q_qty)})",
                )
            elif row["unit_price"] > q_price:
                return (
                    "Preço Anormal",
                    f"Preço acima do normal: R$ {row['unit_price']:.2f} (limite: R$ {q_price:.2f})",
                )
            elif row["faturamento"] > q_fat:
                return (
                    "Valor Total Alto",
                    f"Faturamento anormal: R$ {row['faturamento']:.2f} (limite: R$ {q_fat:.2f})",
                )
            else:
                return "Combinação Suspeita", f"Padrão anômalo detectado"

        for idx in anomalies.index:
            row = anomalies.loc[idx]
            tipo, motivo = categorize_fraud(row, q95_qty, q95_price, q95_faturamento)
            anomalies.at[idx, "tipo_fraude"] = tipo
            anomalies.at[idx, "motivo"] = motivo

        c1, c2 = st.columns([3, 1])
        with c1:
            fig = px.scatter(
                df_ai,
                x="faturamento",
                y="unit_price",
                color=df_ai["anomaly_score"].astype(str),
                color_discrete_map={"-1": "red", "1": "blue"},
                log_x=True,
                log_y=True,
                title="Clusterização de Risco",
                hover_data=["order_id", "quantity", "faturamento"],
            )
            st.plotly_chart(fig, width="stretch")
        with c2:
            st.metric("Suspeitas Detectadas", len(anomalies))

        if len(anomalies) > 0:
            st.divider()
            st.markdown("### Detalhes das Anomalias Detectadas")

            anomalies_display = anomalies.sort_values(
                "faturamento", ascending=False
            ).copy()

            if "product_id" in anomalies_display.columns:
                anomalies_display = anomalies_display[
                    [
                        "order_id",
                        "product_id",
                        "quantity",
                        "unit_price",
                        "faturamento",
                        "tipo_fraude",
                        "motivo",
                    ]
                ]
                anomalies_display.columns = [
                    "Order ID",
                    "Produto ID",
                    "Quantidade",
                    "Preço Unit.",
                    "Faturamento",
                    "Tipo Fraude",
                    "Motivo",
                ]
            else:
                anomalies_display = anomalies_display[
                    [
                        "order_id",
                        "quantity",
                        "unit_price",
                        "faturamento",
                        "tipo_fraude",
                        "motivo",
                    ]
                ]
                anomalies_display.columns = [
                    "Order ID",
                    "Quantidade",
                    "Preço Unit.",
                    "Faturamento",
                    "Tipo Fraude",
                    "Motivo",
                ]

            st.dataframe(anomalies_display, width="stretch", hide_index=True)

            csv = anomalies_display.to_csv(index=False)
            st.download_button(
                label="Baixar Anomalias (CSV)",
                data=csv,
                file_name="anomalias_detectadas.csv",
                mime="text/csv",
            )
        else:
            st.success("Nenhuma anomalia detectada neste período!")
    else:
        st.info("Dados insuficientes para IA.")
