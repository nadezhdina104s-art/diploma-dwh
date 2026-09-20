# 06. Data Quality

## 6.1. Правила DQ

| № | Правило | Действие | Реализация |
|---|---|---|---|
| 1 | invoice_id NOT NULL | reject | проверка в pandas |
| 2 | invoice_id уникален | dedup | drop_duplicates |
| 3 | quantity > 0 | reject | проверка в pandas |
| 4 | tax_5pct = cogs × 0.05 (±0.01) | warning | флаг dq_tax_ok |
| 5 | total = cogs + tax_5pct (±0.01) | warning | флаг dq_total_ok |
| 6 | rating в диапазоне [0, 10] | reject | проверка в pandas |

## 6.2. Отчёт dq_report

Таблица dq_report заполняется на каждом запуске задачи dq_check:

```sql
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
6.3. Результаты проверки
По датасету sales.csv (1000 строк):

Метрика	Значение
row_count	1000
null_invoice_id	0
dup_invoice_id	0
negative_qty	0
tax_mismatch	0
total_mismatch	0
rating_out_of_rng	0
Датасет прошёл все проверки — 100% валидных записей.

6.4. Логика отбраковки
Если null_invoice_id > 0 или dup_invoice_id > 0, задача
dq_check бросает ValueError и останавливает DAG. Downstream
задачи (load_nds, load_dds, build_marts) не выполняются.

6.5. Мониторинг качества
Запрос для проверки качества по всем запускам:

sql
SELECT run_date, row_count, tax_mismatch, total_mismatch,
       rating_out_of_rng
FROM dq_report
ORDER BY report_id DESC;