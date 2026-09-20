=============================== НАЧАЛО README ===============================
# Diploma DWH Project: Sales Analytics

Дипломный проект по профессии «Инженер данных». Документация ETL-процессов
на основе датасета sales.csv (1000 транзакций, Q1 2019, 3 филиала в Мьянме).

## Архитектура
sales.csv → [Airflow DAG] → NDS (3NF) → DDS (звезда) → Marts → Tableau
↓
Data Quality + etl_run_log

text

## Стек

- Python 3.10 — ETL (pandas, SQLAlchemy)
- PostgreSQL 15 — хранилище (NDS + DDS + Marts)
- Apache Airflow 2.8 — оркестрация
- Docker Compose — развёртывание
- Tableau Public — визуализация

## Структура репозитория
diploma-dwh/
├── dags/ # Airflow DAG
├── etl/ # Python-скрипты ETL
├── sql/ # SQL-скрипты (DDL, marts)
├── docs/ # Документация проекта
├── data/ # Исходный CSV
├── tableau/ # CSV для Tableau + .twbx
├── logs/ # Логи Airflow
├── docker-compose.yml
└── requirements.txt

text

## Быстрый старт

```bash
git clone <repo>
cd diploma-dwh
docker compose up -d
# Airflow UI: http://localhost:8080 (admin/admin)
# PostgreSQL: localhost:5432 (airflow/airflow, БД dwh)
Далее — Trigger DAG sales_etl_pipeline в Airflow UI.

## Документация

- [Архитектура](docs/01_architecture.md)
- [Источник данных](docs/02_source_data.md)
- [Слой NDS](docs/03_nds.md)
- [Слой DDS](docs/04_dds.md)
- [ETL-процессы](docs/05_etl_processes.md)
- [Data Quality](docs/06_data_quality.md)
- [Витрины](docs/07_marts.md)
- [Дашборды](docs/08_dashboards.md)
- [Развёртывание](docs/09_deployment.md)


=============================== КОНЕЦ README