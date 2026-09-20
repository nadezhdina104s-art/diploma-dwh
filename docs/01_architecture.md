# 01. Архитектура решения

## 1.1. Общая схема
┌─────────────┐
│ sales.csv │ (1000 строк, 17 полей, Q1 2019)
└──────┬──────┘
│
▼
┌─────────────────────────────────────────────────────────┐
│ Apache Airflow DAG │
│ sales_etl_pipeline │
│ │
│ extract → transform → dq_check → load_nds → load_dds │
│ │ │ │ │
│ ▼ ▼ ▼ │
│ dq_report nds_* dim_/fact_ │
│ │ │
│ └→ build_marts ──→ mv_
└─────────────────────────────────────────────────────────┘
│
▼
┌─────────────────┐
│ PostgreSQL │
│ БД: dwh │
│ ├── NDS │ (3NF, 7 таблиц)
│ ├── DDS │ (звезда, 7 таблиц)
│ ├── Marts │ (4 materialized view)
│ └── Metadata │ (etl_run_log, dq_report)
└────────┬────────┘
│
▼
┌─────────────────┐
│ Tableau Public │
│ dashboards │
└─────────────────┘

text

## 1.2. Слои хранилища

| Слой | Назначение | Модель | Таблиц |
|---|---|---|---|
| NDS | Нормализованное хранилище | 3NF | 7 |
| DDS | Схема «звезда» для аналитики | Star Schema | 7 |
| Marts | Витрины данных | Materialized Views | 4 |
| Metadata | Метаданные и качество | — | 2 |

## 1.3. Технологический стек

| Компонент | Технология | Версия | Назначение |
|---|---|---|---|
| Язык ETL | Python | 3.10 | Extract, Transform |
| Библиотеки | pandas, SQLAlchemy | 2.1.4, 2.0.25 | Обработка данных |
| СУБД | PostgreSQL | 15 | Хранилище |
| Оркестрация | Apache Airflow | 2.8.1 | Планирование ETL |
| Контейнеризация | Docker Compose | 5.x | Развёртывание |
| BI | Tableau Public | 2026.1 | Визуализация |

## 1.4. Поток данных

1. Extract: CSV читается в pandas DataFrame.
2. Transform: даты/время приводятся к ISO, колонки переименовываются,
   выполняется расчёт контрольных полей dq_tax_ok, dq_total_ok.
3. Data Quality: проверяются 6 правил (NOT NULL, уникальность,
   бизнес-правила). Результат пишется в dq_report.
4. Load NDS: данные раскладываются в 3NF — 5 справочников + 2 факта
   (nds_invoice, nds_invoice_line).
5. Load DDS: строятся измерения (dim_*) и факт fact_sales.
6. Build Marts: обновляются materialized views.
7. Logging: на каждом шаге пишется строка в etl_run_log
   со статусом RUNNING → SUCCESS/FAILED.

## 1.5. Идемпотентность

Все INSERT-операции используют ON CONFLICT DO NOTHING или
WHERE NOT EXISTS. Повторный запуск DAG не создаёт дублей.
