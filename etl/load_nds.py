"""
etl/load_nds.py
Загрузка нормализованных данных в NDS (3NF).
Все справочники обрабатываются идемпотентно через ON CONFLICT DO NOTHING.
"""
import logging
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Хелперы
# ---------------------------------------------------------------------------
def _get_or_create(conn, table: str, id_col: str, name_col: str, value: str) -> int:
    """Возвращает id из справочника, создавая запись при необходимости."""
    row = conn.execute(
        text(f"SELECT {id_col} FROM {table} WHERE {name_col} = :v"),
        {"v": value}
    ).fetchone()
    if row:
        return row[0]

    new_id = conn.execute(
        text(f"""
            INSERT INTO {table} ({name_col})
            VALUES (:v)
            RETURNING {id_col}
        """),
        {"v": value}
    ).scalar()
    return new_id


# ---------------------------------------------------------------------------
# Загрузка справочников
# ---------------------------------------------------------------------------
def load_dim_branch(conn, df: pd.DataFrame) -> None:
    """branch_code ↔ city — отношение 1:1."""
    pairs = df[["branch_code", "city"]].drop_duplicates()
    for _, r in pairs.iterrows():
        conn.execute(text("""
            INSERT INTO nds_branch (branch_code, city)
            VALUES (:b, :c)
            ON CONFLICT (branch_code) DO NOTHING
        """), {"b": r.branch_code, "c": r.city})
    logger.info(f"nds_branch: обработано {len(pairs)} записей")


def load_dim_customer_type(conn, df: pd.DataFrame) -> None:
    for v in df["customer_type"].dropna().unique():
        _get_or_create(conn, "nds_customer_type",
                       "customer_type_id", "customer_type_name", v)
    logger.info(f"nds_customer_type: {df['customer_type'].nunique()} уникальных")


def load_dim_gender(conn, df: pd.DataFrame) -> None:
    for v in df["gender"].dropna().unique():
        _get_or_create(conn, "nds_gender",
                       "gender_id", "gender_name", v)
    logger.info(f"nds_gender: {df['gender'].nunique()} уникальных")


def load_dim_payment(conn, df: pd.DataFrame) -> None:
    for v in df["payment"].dropna().unique():
        _get_or_create(conn, "nds_payment",
                       "payment_id", "payment_name", v)
    logger.info(f"nds_payment: {df['payment'].nunique()} уникальных")


def load_dim_product_line(conn, df: pd.DataFrame) -> None:
    for v in df["product_line"].dropna().unique():
        _get_or_create(conn, "nds_product_line",
                       "product_line_id", "product_line_name", v)
    logger.info(f"nds_product_line: {df['product_line'].nunique()} уникальных")


# ---------------------------------------------------------------------------
# Загрузка фактов
# ---------------------------------------------------------------------------
def load_invoices(conn, df: pd.DataFrame) -> int:
    """Загружает заголовки чеков в nds_invoice."""
    loaded = 0
    for _, r in df.iterrows():
        branch_id = conn.execute(
            text("SELECT branch_id FROM nds_branch WHERE branch_code = :c"),
            {"c": r.branch_code}
        ).scalar()

        ct_id = conn.execute(
            text("SELECT customer_type_id FROM nds_customer_type WHERE customer_type_name = :n"),
            {"n": r.customer_type}
        ).scalar()

        g_id = conn.execute(
            text("SELECT gender_id FROM nds_gender WHERE gender_name = :n"),
            {"n": r.gender}
        ).scalar()

        p_id = conn.execute(
            text("SELECT payment_id FROM nds_payment WHERE payment_name = :n"),
            {"n": r.payment}
        ).scalar()

        result = conn.execute(text("""
            INSERT INTO nds_invoice
                (invoice_id, branch_id, customer_type_id, gender_id,
                 payment_id, sale_date, sale_time, rating)
            VALUES (:inv, :br, :ct, :g, :p, :d, :t, :r)
            ON CONFLICT (invoice_id) DO NOTHING
        """), {
            "inv": r.invoice_id,
            "br":  branch_id,
            "ct":  ct_id,
            "g":   g_id,
            "p":   p_id,
            "d":   r.sale_date,
            "t":   r.sale_time,
            "r":   float(r.rating) if pd.notna(r.rating) else None,
        })
        loaded += result.rowcount
    logger.info(f"nds_invoice: вставлено {loaded} записей")
    return loaded


def load_invoice_lines(conn, df: pd.DataFrame) -> int:
    """Загружает товарные позиции в nds_invoice_line."""
    loaded = 0
    for _, r in df.iterrows():
        pl_id = conn.execute(
            text("SELECT product_line_id FROM nds_product_line WHERE product_line_name = :n"),
            {"n": r.product_line}
        ).scalar()

        result = conn.execute(text("""
            INSERT INTO nds_invoice_line
                (invoice_id, product_line_id, unit_price, quantity,
                 tax_5pct, total, cogs, gross_margin_pct, gross_income)
            SELECT :inv, :pl, :up, :q, :tax, :tot, :cogs, :gmp, :gi
            WHERE NOT EXISTS (
                SELECT 1 FROM nds_invoice_line
                WHERE invoice_id = :inv AND product_line_id = :pl
            )
        """), {
            "inv":  r.invoice_id,
            "pl":   pl_id,
            "up":   float(r.unit_price),
            "q":    int(r.quantity),
            "tax":  float(r.tax_5pct),
            "tot":  float(r.total),
            "cogs": float(r.cogs),
            "gmp":  float(r.gross_margin_pct) if pd.notna(r.gross_margin_pct) else None,
            "gi":   float(r.gross_income) if pd.notna(r.gross_income) else None,
        })
        loaded += result.rowcount
    logger.info(f"nds_invoice_line: вставлено {loaded} записей")
    return loaded


# ---------------------------------------------------------------------------
# Точка входа
# ---------------------------------------------------------------------------
def load_nds(df: pd.DataFrame, engine: Engine) -> dict:
    """
    Основная функция загрузки NDS.
    Возвращает словарь со счётчиками загрузки.
    """
    started = datetime.now()
    stats = {"started": started.isoformat()}

    with engine.begin() as conn:
        # 1. Справочники (порядок важен из-за FK)
        load_dim_branch(conn, df)
        load_dim_customer_type(conn, df)
        load_dim_gender(conn, df)
        load_dim_payment(conn, df)
        load_dim_product_line(conn, df)

        # 2. Факты
        stats["invoices_loaded"] = load_invoices(conn, df)
        stats["lines_loaded"]    = load_invoice_lines(conn, df)

    stats["finished"]  = datetime.now().isoformat()
    stats["duration_s"] = (datetime.now() - started).total_seconds()
    logger.info(f"NDS загружен за {stats['duration_s']:.2f} сек")
    return stats


if __name__ == "__main__":
    from etl.extract import extract_csv
    from etl.transform import transform

    ENGINE = create_engine("postgresql://user:pass@localhost:5432/dwh")
    raw = extract_csv("sales.csv")
    clean = transform(raw)
    load_nds(clean, ENGINE)