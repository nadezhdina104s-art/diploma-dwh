"""
etl/load_dds.py
Построение схемы «звезда» из NDS.
Все вставки идемпотентны.
"""
import logging
from datetime import datetime, date, time, timedelta

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. dim_date — генерируется один раз на весь диапазон дат
# ---------------------------------------------------------------------------
def load_dim_date(conn) -> int:
    """Генерирует календарь от min(sale_date) до max(sale_date)."""
    bounds = conn.execute(text(
        "SELECT MIN(sale_date), MAX(sale_date) FROM nds_invoice"
    )).fetchone()

    if not bounds or not bounds[0]:
        logger.warning("dim_date: нет данных в nds_invoice")
        return 0

    start, end = bounds
    d = start
    rows = []
    while d <= end:
        rows.append({
            "key":       int(d.strftime("%Y%m%d")),
            "full_date": d,
            "day":       d.day,
            "month":     d.month,
            "month_name": d.strftime("%B"),
            "quarter":   (d.month - 1) // 3 + 1,
            "year":      d.year,
            "dow":       d.weekday(),          # 0 = Monday
            "day_name":  d.strftime("%A"),
            "is_weekend": d.weekday() >= 5,
        })
        d += timedelta(days=1)

    for r in rows:
        conn.execute(text("""
            INSERT INTO dim_date
                (date_key, full_date, day, month, month_name,
                 quarter, year, day_of_week, day_name, is_weekend)
            VALUES (:key, :full_date, :day, :month, :month_name,
                    :quarter, :year, :dow, :day_name, :is_weekend)
            ON CONFLICT (date_key) DO NOTHING
        """), r)

    logger.info(f"dim_date: сгенерировано {len(rows)} дней")
    return len(rows)


# ---------------------------------------------------------------------------
# 2. dim_time — 1440 минут в сутках
# ---------------------------------------------------------------------------
def load_dim_time(conn) -> int:
    """Генерирует все минуты суток 00:00 – 23:59."""
    rows = []
    for h in range(24):
        for m in range(60):
            if 5 <= h < 12:
                part = "Morning"
            elif 12 <= h < 17:
                part = "Afternoon"
            elif 17 <= h < 22:
                part = "Evening"
            else:
                part = "Night"

            rows.append({
                "key":   h * 100 + m,
                "time":  time(h, m),
                "hour":  h,
                "minute": m,
                "part":  part,
            })

    for r in rows:
        conn.execute(text("""
            INSERT INTO dim_time (time_key, full_time, hour, minute, day_part)
            VALUES (:key, :time, :hour, :minute, :part)
            ON CONFLICT (time_key) DO NOTHING
        """), r)

    logger.info(f"dim_time: сгенерировано {len(rows)} минут")
    return len(rows)


# ---------------------------------------------------------------------------
# 3. dim_branch — из nds_branch
# ---------------------------------------------------------------------------
def load_dim_branch(conn) -> int:
    result = conn.execute(text("""
        INSERT INTO dim_branch (branch_code, city)
        SELECT b.branch_code, b.city
        FROM nds_branch b
        WHERE NOT EXISTS (
            SELECT 1 FROM dim_branch d WHERE d.branch_code = b.branch_code
        )
    """))
    logger.info(f"dim_branch: {result.rowcount} записей")
    return result.rowcount


# ---------------------------------------------------------------------------
# 4. dim_customer — декартово (customer_type × gender)
# ---------------------------------------------------------------------------
def load_dim_customer(conn) -> int:
    result = conn.execute(text("""
        INSERT INTO dim_customer (customer_type, gender)
        SELECT DISTINCT ct.customer_type_name, g.gender_name
        FROM nds_customer_type ct
        CROSS JOIN nds_gender g
        WHERE NOT EXISTS (
            SELECT 1 FROM dim_customer dc
            WHERE dc.customer_type = ct.customer_type_name
              AND dc.gender = g.gender_name
        )
    """))
    logger.info(f"dim_customer: {result.rowcount} записей")
    return result.rowcount


# ---------------------------------------------------------------------------
# 5. dim_product — из nds_product_line
# ---------------------------------------------------------------------------
def load_dim_product(conn) -> int:
    result = conn.execute(text("""
        INSERT INTO dim_product (product_line_name)
        SELECT pl.product_line_name
        FROM nds_product_line pl
        WHERE NOT EXISTS (
            SELECT 1 FROM dim_product p
            WHERE p.product_line_name = pl.product_line_name
        )
    """))
    logger.info(f"dim_product: {result.rowcount} записей")
    return result.rowcount


# ---------------------------------------------------------------------------
# 6. dim_payment — из nds_payment
# ---------------------------------------------------------------------------
def load_dim_payment(conn) -> int:
    result = conn.execute(text("""
        INSERT INTO dim_payment (payment_name)
        SELECT p.payment_name
        FROM nds_payment p
        WHERE NOT EXISTS (
            SELECT 1 FROM dim_payment dp WHERE dp.payment_name = p.payment_name
        )
    """))
    logger.info(f"dim_payment: {result.rowcount} записей")
    return result.rowcount


# ---------------------------------------------------------------------------
# 7. fact_sales — соединение NDS-таблиц
# ---------------------------------------------------------------------------
def load_fact_sales(conn) -> int:
    """Одна строка fact_sales = один чек (одна товарная позиция)."""
    result = conn.execute(text("""
        INSERT INTO fact_sales (
            invoice_id, date_key, time_key,
            branch_key, customer_key, product_key, payment_key,
            unit_price, quantity, tax_5pct, total, cogs, gross_income, rating
        )
        SELECT
            i.invoice_id,
            TO_CHAR(i.sale_date, 'YYYYMMDD')::INT                        AS date_key,
            (EXTRACT(HOUR FROM i.sale_time) * 100
             + EXTRACT(MINUTE FROM i.sale_time))::INT                    AS time_key,
            db.branch_key,
            dc.customer_key,
            dp.product_key,
            dpm.payment_key,
            l.unit_price, l.quantity, l.tax_5pct, l.total,
            l.cogs, l.gross_income, i.rating
        FROM nds_invoice i
        JOIN nds_invoice_line l    ON l.invoice_id        = i.invoice_id
        JOIN nds_branch        nb  ON nb.branch_id        = i.branch_id
        JOIN nds_customer_type nct ON nct.customer_type_id = i.customer_type_id
        JOIN nds_gender        ng  ON ng.gender_id        = i.gender_id
        JOIN nds_payment       np  ON np.payment_id       = i.payment_id
        JOIN nds_product_line  npl ON npl.product_line_id = l.product_line_id

        JOIN dim_branch   db  ON db.branch_code       = nb.branch_code
        JOIN dim_customer dc  ON dc.customer_type     = nct.customer_type_name
                              AND dc.gender           = ng.gender_name
        JOIN dim_product  dp  ON dp.product_line_name = npl.product_line_name
        JOIN dim_payment  dpm ON dpm.payment_name     = np.payment_name

        WHERE NOT EXISTS (
            SELECT 1 FROM fact_sales f WHERE f.invoice_id = i.invoice_id
        )
    """))
    logger.info(f"fact_sales: вставлено {result.rowcount} строк")
    return result.rowcount


# ---------------------------------------------------------------------------
# Точка входа
# ---------------------------------------------------------------------------
def load_dds(engine: Engine) -> dict:
    started = datetime.now()
    stats = {"started": started.isoformat()}

    with engine.begin() as conn:
        # 1. Измерения
        stats["dim_date"]     = load_dim_date(conn)
        stats["dim_time"]     = load_dim_time(conn)
        stats["dim_branch"]   = load_dim_branch(conn)
        stats["dim_customer"] = load_dim_customer(conn)
        stats["dim_product"]  = load_dim_product(conn)
        stats["dim_payment"]  = load_dim_payment(conn)

        # 2. Факт
        stats["fact_sales"]   = load_fact_sales(conn)

    stats["finished"]   = datetime.now().isoformat()
    stats["duration_s"] = (datetime.now() - started).total_seconds()
    logger.info(f"DDS загружен за {stats['duration_s']:.2f} сек")
    return stats


if __name__ == "__main__":
    ENGINE = create_engine("postgresql://user:pass@localhost:5432/dwh")
    load_dds(ENGINE)