# 07. Витрины данных

## 7.1. Общее

Витрины реализованы как materialized views — они кэшируют
результат тяжёлых JOIN-ов и агрегаций. Обновляются задачей
build_marts в DAG (команда REFRESH MATERIALIZED VIEW).

## 7.2. mv_sales_by_product

Гранулярность: товарная линейка.

```sql
SELECT product_line_name,
       COUNT(*) AS sales_cnt,
       SUM(quantity) AS qty,
       SUM(total) AS revenue,
       AVG(unit_price) AS avg_price,
       AVG(rating) AS avg_rating
FROM fact_sales f
JOIN dim_product p ON p.product_key = f.product_key
GROUP BY product_line_name;
Результат (6 строк):

product_line_name	sales_cnt	qty	revenue	avg_rating
Food and beverages	174	952	56 144.84	7.11
Sports and travel	166	920	55 122.83	6.92
Electronic accessories	170	971	54 337.53	6.92
Fashion accessories	178	902	54 305.90	7.03
Home and lifestyle	160	911	53 861.91	6.84
Health and beauty	152	854	49 193.74	7.00
7.3. mv_sales_by_branch
Гранулярность: филиал × месяц.

sql
SELECT b.branch_code, b.city, d.year, d.month,
       COUNT(DISTINCT f.invoice_id) AS invoices_cnt,
       SUM(f.quantity) AS items_sold,
       SUM(f.total) AS revenue,
       SUM(f.gross_income) AS gross_income,
       AVG(f.rating) AS avg_rating
FROM fact_sales f
JOIN dim_branch b ON b.branch_key = f.branch_key
JOIN dim_date d ON d.date_key = f.date_key
GROUP BY b.branch_code, b.city, d.year, d.month;
Результат: 9 строк (3 филиала × 3 месяца).

7.4. mv_payment_customer
Гранулярность: способ оплаты × тип клиента × пол.

sql
SELECT pay.payment_name, c.customer_type, c.gender,
       COUNT(*) AS cnt, SUM(f.total) AS revenue
FROM fact_sales f
JOIN dim_payment pay ON pay.payment_key = f.payment_key
JOIN dim_customer c ON c.customer_key = f.customer_key
GROUP BY pay.payment_name, c.customer_type, c.gender;
7.5. mv_time_patterns
Гранулярность: часть дня × день недели × выходной.

sql
SELECT t.day_part, d.day_name, d.is_weekend,
       COUNT(*) AS cnt, SUM(f.total) AS revenue
FROM fact_sales f
JOIN dim_time t ON t.time_key = f.time_key
JOIN dim_date d ON d.date_key = f.date_key
GROUP BY t.day_part, d.day_name, d.is_weekend;
7.6. Ключевые метрики (KPI)
Метрика	Формула	Значение
Total Revenue	SUM(total)	322 967
Gross Income	SUM(gross_income)	15 379
Items Sold	SUM(quantity)	5 510
Invoices	COUNT(DISTINCT invoice_id)	1000
Avg Check	SUM(total)/COUNT	322.97
Avg Rating	AVG(rating)	6.97
