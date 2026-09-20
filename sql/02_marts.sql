-- Витрина: продажи по филиалам
CREATE MATERIALIZED VIEW mv_sales_by_branch AS
SELECT
    b.branch_code,
    b.city,
    d.year,
    d.month,
    COUNT(DISTINCT f.invoice_id) AS invoices_cnt,
    SUM(f.quantity)              AS items_sold,
    SUM(f.total)                 AS revenue,
    SUM(f.gross_income)          AS gross_income,
    AVG(f.rating)                AS avg_rating
FROM fact_sales f
JOIN dim_branch b ON b.branch_key = f.branch_key
JOIN dim_date   d ON d.date_key   = f.date_key
GROUP BY b.branch_code, b.city, d.year, d.month;
CREATE UNIQUE INDEX mv_branch_idx ON mv_sales_by_branch(branch_code, year, month);
-- Витрина: продажи по товарным линейкам
CREATE MATERIALIZED VIEW mv_sales_by_product AS
SELECT
    p.product_line_name,
    COUNT(*)          AS sales_cnt,
    SUM(f.quantity)   AS qty,
    SUM(f.total)      AS revenue,
    AVG(f.unit_price) AS avg_price,
    AVG(f.rating)     AS avg_rating
FROM fact_sales f
JOIN dim_product p ON p.product_key = f.product_key
GROUP BY p.product_line_name;
CREATE UNIQUE INDEX mv_product_idx ON mv_sales_by_product(product_line_name);
-- Витрина: оплата × клиент
CREATE MATERIALIZED VIEW mv_payment_customer AS
SELECT
    pay.payment_name,
    c.customer_type,
    c.gender,
    COUNT(*)     AS cnt,
    SUM(f.total) AS revenue
FROM fact_sales f
JOIN dim_payment  pay ON pay.payment_key = f.payment_key
JOIN dim_customer c   ON c.customer_key  = f.customer_key
GROUP BY pay.payment_name, c.customer_type, c.gender;
CREATE UNIQUE INDEX mv_pay_cust_idx
    ON mv_payment_customer(payment_name, customer_type, gender);
-- Витрина: временные паттерны
CREATE MATERIALIZED VIEW mv_time_patterns AS
SELECT
    t.day_part,
    d.day_name,
    d.is_weekend,
    COUNT(*)     AS cnt,
    SUM(f.total) AS revenue
FROM fact_sales f
JOIN dim_time t ON t.time_key = f.time_key
JOIN dim_date d ON d.date_key = f.date_key
GROUP BY t.day_part, d.day_name, d.is_weekend;
CREATE UNIQUE INDEX mv_time_idx
    ON mv_time_patterns(day_part, day_name, is_weekend);
