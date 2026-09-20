# 09. Развёртывание

## 9.1. Требования

| Компонент | Минимум |
|---|---|
| ОС | Windows 10/11, Linux, macOS |
| Docker Desktop | 4.0+ |
| RAM | 4 ГБ свободно (лучше 8 ГБ) |
| Диск | 5 ГБ свободно |
| Интернет | Для скачивания образов |

## 9.2. Установка

### Шаг 1. Клонировать проект

```bash
git clone <repo>
cd diploma-dwh
Шаг 2. Проверить структуру
bash
tree
# dags/ etl/ sql/ data/ tableau/ docs/ docker-compose.yml
Шаг 3. Запустить контейнеры
bash
docker compose up -d
Первый запуск занимает 5–10 минут (скачивание образов ~2 ГБ).

Шаг 4. Проверить контейнеры
bash
docker compose ps
Ожидаемо:

postgres-1 — Up (healthy)

airflow-scheduler-1 — Up

airflow-webserver-1 — Up

airflow-init-1 — Exited (0)

Шаг 5. Открыть Airflow
URL: http://localhost:8080

Логин: admin

Пароль: admin

9.3. Первый запуск ETL
В Airflow UI найти DAG sales_etl_pipeline.

Включить тумблер Unpause.

Нажать Trigger DAG.

Перейти на вкладку Grid — наблюдать за выполнением.

9.4. Проверка результата
bash
docker exec -it diploma-dwh-postgres-1 psql -U airflow -d dwh -c "\dt"
docker exec -it diploma-dwh-postgres-1 psql -U airflow -d dwh -c "SELECT COUNT(*) FROM fact_sales;"
Ожидаемо: 16 таблиц, 1000 записей в fact_sales.

9.5. Подключение Tableau
Вариант 1 — к PostgreSQL:

Server: localhost, Port: 5432

Database: dwh, User: airflow, Password: airflow

Вариант 2 — к CSV:

Открыть tableau/fact_sales_full.csv

9.6. Остановка
bash
docker compose down       # остановить, данные сохранить
docker compose down -v    # остановить и удалить volumes
9.7. Устранение типовых проблем
Проблема	Решение
Postgres падает с exit 3	Проверить docker compose logs postgres. Часто — BOM в SQL-файле, удалить через UTF8Encoding($false).
Airflow DAG не виден	Подождать 30 сек, обновить страницу. Проверить airflow dags list-import-errors.
Ошибка Connection not found	Создать коннекшн: airflow connections add dwh_postgres ...
rows_loaded = 0 в etl_run_log	Нормально: артефакт psycopg2 с ON CONFLICT DO NOTHING. Данные загружены.
