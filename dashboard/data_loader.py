from typing import Tuple
import pandas as pd
from core.data_utils import DataLoader
from core.exceptions import DataSourceUnavailableError


def load_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load data from PostgreSQL with optimized queries."""
    try:
        return DataLoader.load_tables()
    except Exception as e:
        raise DataSourceUnavailableError(f"Failed to load data from PostgreSQL: {e}")


def process_data(
    _orders: pd.DataFrame,
    _items: pd.DataFrame,
    _products: pd.DataFrame,
    _customers: pd.DataFrame,
) -> pd.DataFrame:
    """Process and merge order, item, product, and customer data."""
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

    estado_map = {
        "Norte": ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
        "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
        "Centro-Oeste": ["DF", "GO", "MT", "MS"],
        "Sudeste": ["ES", "MG", "RJ", "SP"],
        "Sul": ["PR", "RS", "SC"],
    }
    uf_to_regiao = {uf: reg for reg, ufs in estado_map.items() for uf in ufs}
    df["region"] = df["state"].map(uf_to_regiao).fillna(df["region"])

    return df
