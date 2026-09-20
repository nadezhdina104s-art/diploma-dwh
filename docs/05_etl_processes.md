# 05. ETL-процессы

## 5.1. DAG Airflow

DAG ID: sales_etl_pipeline
Schedule: @daily
Owner: data_engineer
Файл: dags/sales_etl_dag.py

## 5.2. Граф задач
extract → transform → dq_check → load_nds → load_dds → build_marts

text

| № | Task | Что делает | Выход |
|---|---|---|---|
| 1 | extract | Читает CSV, кладёт parquet в /tmp | /tmp/sales_raw_*.parquet |
| 2 | transform | Приводит типы, переименовывает колонки, считает контрольные поля | /tmp/sales_clean_*.parquet |
| 3 | dq_check | Проверяет 6 правил DQ, пишет в dq_report | запись в dq_report |
| 4 | load_nds | Загружает NDS (3NF) | nds_* заполнены |
| 5 | load_dds | Строит звезду | fact_sales + dim_* |
| 6 | build_marts | REFRESH materialized views | mv_* обновлены |

## 5.3. Логика обработки ошибок

Каждая задача обёрнута декоратором etl_task(), который:

1. Пишет в etl_run_log строку со статусом RUNNING.
2. Выполняет задачу.
3. При успехе — обновляет статус на SUCCESS + rows_loaded + duration_s.
4. При исключении — обновляет статус на FAILED + error_message
   и пробрасывает исключение дальше.

Retry policy:
- retries = 2
- retry_delay = 3 min
- При падении dq_check — DAG останавливается (downstream задачи не запускаются).

## 5.4. Идемпотентность

Все INSERT используют ON CONFLICT DO NOTHING.
Повторный запуск DAG не создаёт дублей.

## 5.5. Параметры подключения

Хранится в Airflow Connection:
- Conn Id: dwh_postgres
- Conn Type: Postgres
- Host: postgres
- Schema: dwh
- Login: airflow
- Port: 5432

## 5.6. Мониторинг

- Airflow UI: Grid view по адресу http://localhost:8080
- SQL-запрос для проверки статуса последних запусков:

```sql
SELECT run_id, task_id, status, rows_loaded, duration_s,
       LEFT(error_message, 200) AS err
FROM etl_run_log
ORDER BY run_id DESC
LIMIT 20;