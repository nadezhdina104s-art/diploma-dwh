-- РЎРѕР·РґР°С‘Рј РѕС‚РґРµР»СЊРЅСѓСЋ Р‘Р” РґР»СЏ С…СЂР°РЅРёР»РёС‰Р°
CREATE DATABASE dwh;
\c dwh

-- ============ NDS ============
CREATE TABLE nds_branch (
    branch_id      SERIAL PRIMARY KEY,
    branch_code    VARCHAR(1)  NOT NULL UNIQUE,
    city           VARCHAR(50) NOT NULL
);

CREATE TABLE nds_customer_type (
    customer_type_id   SERIAL PRIMARY KEY,
    customer_type_name VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE nds_gender (
    gender_id   SERIAL PRIMARY KEY,
    gender_name VARCHAR(10) NOT NULL UNIQUE
);

CREATE TABLE nds_payment (
    payment_id   SERIAL PRIMARY KEY,
    payment_name VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE nds_product_line (
    product_line_id   SERIAL PRIMARY KEY,
    product_line_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE nds_invoice (
    invoice_id         VARCHAR(20) PRIMARY KEY,
    branch_id          INT NOT NULL REFERENCES nds_branch(branch_id),
    customer_type_id   INT NOT NULL REFERENCES nds_customer_type(customer_type_id),
    gender_id          INT NOT NULL REFERENCES nds_gender(gender_id),
    payment_id         INT NOT NULL REFERENCES nds_payment(payment_id),
    sale_date          DATE NOT NULL,
    sale_time          TIME NOT NULL,
    rating             NUMERIC(3,1),
    load_dt            TIMESTAMP DEFAULT NOW()
);

CREATE TABLE nds_invoice_line (
    invoice_line_id   SERIAL PRIMARY KEY,
    invoice_id        VARCHAR(20) NOT NULL REFERENCES nds_invoice(invoice_id),
    product_line_id   INT NOT NULL REFERENCES nds_product_line(product_line_id),
    unit_price        NUMERIC(10,2) NOT NULL,
    quantity          INT NOT NULL,
    tax_5pct          NUMERIC(10,4) NOT NULL,
    total             NUMERIC(10,4) NOT NULL,
    cogs              NUMERIC(10,2) NOT NULL,
    gross_margin_pct  NUMERIC(12,9),
    gross_income      NUMERIC(10,4),
    load_dt           TIMESTAMP DEFAULT NOW()
);

-- ============ DDS ============
CREATE TABLE dim_date (
    date_key     INT PRIMARY KEY,
    full_date    DATE NOT NULL,
    day          INT  NOT NULL,
    month        INT  NOT NULL,
    month_name   VARCHAR(20),
    quarter      INT  NOT NULL,
    year         INT  NOT NULL,
    day_of_week  INT  NOT NULL,
    day_name     VARCHAR(20),
    is_weekend   BOOLEAN
);

CREATE TABLE dim_time (
    time_key   INT PRIMARY KEY,
    full_time  TIME NOT NULL,
    hour       INT  NOT NULL,
    minute     INT  NOT NULL,
    day_part   VARCHAR(20)
);

CREATE TABLE dim_branch (
    branch_key   SERIAL PRIMARY KEY,
    branch_code  VARCHAR(1)  NOT NULL,
    city         VARCHAR(50) NOT NULL
);

CREATE TABLE dim_customer (
    customer_key   SERIAL PRIMARY KEY,
    customer_type  VARCHAR(20) NOT NULL,
    gender         VARCHAR(10) NOT NULL
);

CREATE TABLE dim_product (
    product_key       SERIAL PRIMARY KEY,
    product_line_name VARCHAR(50) NOT NULL
);

CREATE TABLE dim_payment (
    payment_key   SERIAL PRIMARY KEY,
    payment_name  VARCHAR(20) NOT NULL
);

CREATE TABLE fact_sales (
    invoice_id     VARCHAR(20) PRIMARY KEY,
    date_key       INT NOT NULL REFERENCES dim_date(date_key),
    time_key       INT NOT NULL REFERENCES dim_time(time_key),
    branch_key     INT NOT NULL REFERENCES dim_branch(branch_key),
    customer_key   INT NOT NULL REFERENCES dim_customer(customer_key),
    product_key    INT NOT NULL REFERENCES dim_product(product_key),
    payment_key    INT NOT NULL REFERENCES dim_payment(payment_key),
    unit_price     NUMERIC(10,2),
    quantity       INT,
    tax_5pct       NUMERIC(10,4),
    total          NUMERIC(10,4),
    cogs           NUMERIC(10,2),
    gross_income   NUMERIC(10,4),
    rating         NUMERIC(3,1)
);

CREATE INDEX idx_fact_sales_date   ON fact_sales(date_key);
CREATE INDEX idx_fact_sales_branch ON fact_sales(branch_key);
CREATE INDEX idx_fact_sales_prod   ON fact_sales(product_key);

-- ============ РњРµС‚Р°РґР°РЅРЅС‹Рµ / DQ ============
CREATE TABLE etl_run_log (
    run_id        BIGSERIAL PRIMARY KEY,
    dag_id        VARCHAR(200) NOT NULL,
    task_id       VARCHAR(200) NOT NULL,
    run_date      DATE         NOT NULL,
    status        VARCHAR(20)  NOT NULL,
    start_time    TIMESTAMP    NOT NULL,
    end_time      TIMESTAMP,
    duration_s    NUMERIC(10,2),
    rows_loaded   BIGINT,
    error_message TEXT,
    context       JSONB
);

CREATE INDEX idx_etl_log_dag    ON etl_run_log(dag_id, run_date);
CREATE INDEX idx_etl_log_status ON etl_run_log(status);

CREATE TABLE dq_report (
    report_id          BIGSERIAL PRIMARY KEY,
    run_date           DATE NOT NULL,
    row_count          INT,
    null_invoice_id    INT,
    dup_invoice_id     INT,
    negative_qty       INT,
    tax_mismatch       INT,
    total_mismatch     INT,
    rating_out_of_rng  INT,
    created_at         TIMESTAMP DEFAULT NOW()
);
