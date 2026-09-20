# 04. Слой DDS (схема «звезда»)

## 4.1. Назначение

DDS — денормализованная схема «звезда», оптимизированная для
аналитических запросов и BI-инструментов (Tableau).

## 4.2. ERD
┌──────────────┐ ┌──────────────┐
│ dim_date │ │ dim_time │
├──────────────┤ ├──────────────┤
│ date_key(PK) │ │ time_key(PK) │
│ full_date │ │ full_time │
│ day │ │ hour │
│ month │ │ minute │
│ month_name │ │ day_part │
│ quarter │ └──────┬───────┘
│ year │ │
│ day_of_week │ │
│ day_name │ │
│ is_weekend │ │
└──────┬───────┘ │
│ │
│ ┌─────────────────────────┘
▼ ▼
┌────────────────────────────────────────────┐
│ fact_sales │
├────────────────────────────────────────────┤
│ invoice_id (PK) │
│ date_key FK → dim_date │
│ time_key FK → dim_time │
│ branch_key FK → dim_branch │
│ customer_key FK → dim_customer │
│ product_key FK → dim_product │
│ payment_key FK → dim_payment │
│ unit_price, quantity, tax_5pct, total, │
│ cogs, gross_income, rating │
└──┬────────────┬────────────┬────────────┬──┘
│ │ │ │
▼ ▼ ▼ ▼
┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│dim_branch│ │dim_cust │ │dim_product│ │dim_payment│
├─────────┤ ├──────────┤ ├──────────┤ ├──────────┤
│branch_key│ │cust_key │ │prod_key │ │pay_key │
│branch_cd │ │cust_type │ │prod_line │ │pay_name │
│city │ │gender │ └──────────┘ └──────────┘
└──────────┘ └──────────┘


## 4.3. Измерения

| Измерение | Тип | Ключ | Записей | SCD |
|---|---|---|---|---|
| dim_date | Роль | date_key (YYYYMMDD) | ~90 | — |
| dim_time | Роль | time_key (HHMM) | 1440 | — |
| dim_branch | Справочник | branch_key | 3 | SCD1 |
| dim_customer | Справочник | customer_key | 4 | SCD1 |
| dim_product | Справочник | product_key | 6 | SCD1 |
| dim_payment | Справочник | payment_key | 3 | SCD1 |

## 4.4. Факт fact_sales

- Гранулярность: 1 строка = 1 позиция чека.
- Тип: transactional fact table (без периодических снимков).
- Метрики (measures):
  - unit_price — цена за единицу
  - quantity — количество
  - tax_5pct — налог 5%
  - total — итог с налогом
  - cogs — себестоимость
  - gross_income — валовый доход
  - rating — оценка (полуаддитивная)

## 4.5. DDL

Полный DDL — в sql/01_dwh_init.sql, раздел DDS.

Индексы:
- idx_fact_sales_date — ускорение временных срезов
- idx_fact_sales_branch — ускорение по филиалам
- idx_fact_sales_prod — ускорение по товарным линейкам

## 4.6. Итоги загрузки

| Таблица | Строк |
|---|---|
| dim_date | ~90 |
| dim_time | 1440 |
| dim_branch | 3 |
| dim_customer | 4 |
| dim_product | 6 |
| dim_payment | 3 |
| fact_sales | 1000 |
