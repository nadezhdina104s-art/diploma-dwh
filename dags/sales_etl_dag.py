"""
dags/sales_etl_dag.py
ETL-пайплайн sales.csv -> NDS -> DDS -> Marts.
"""
import json
import logging
from datetime import datetime, timedelta
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from sqlalchemy import create_engine
PG_CONN_ID = "dwh_postgres"
CSV_PATH   = "/opt/airflow/data/sales.csv"
logger = logging.getLogger(__name__)
default_args = {
    "owner": "data_engineer",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=3),
    "email_on_failure": False,
}
def _pg_uri():
    """Ленивое получение URI - вызывается только внутри задач."""
    return PostgresHook(postgres_conn_id=PG_CONN_ID).get_uri()
def log_run(dag_id, task_id, run_date, status,
            start_time=None, end_time=None,
            rows_loaded=None, error=None, context=None):
    hook = PostgresHook(postgres_conn_id=PG_CONN_ID)
    duration = None
    if start_time and end_time:
        duration = (end_time - start_time).total_seconds()
    hook.run("""
        INSERT INTO etl_run_log
            (dag_id, task_id, run_date, status,
             start_time, end_time, duration_s,
             rows_loaded, error_message, context)
        VALUES (%s, %s, %s, %s,
                COALESCE(%s, NOW()), %s, %s,
                %s, %s, %s)
    """, parameters=(
        dag_id, task_id, run_date, status,
        start_time, end_time, duration,
        rows_loaded, error,
        json.dumps(context) if context else None,
    ), autocommit=True)
def etl_task(task_id):
    def wrapper(func):
        def inner(**context):
            dag_id   = context["dag"].dag_id
            run_date = context["ds"]
            start    = datetime.now()
            log_run(dag_id, task_id, run_date, "RUNNING", start_time=start)
            try:
                result = func(**context)
                end = datetime.now()
                rows = result.get("rows_loaded") if isinstance(result, dict) else None
                log_run(dag_id, task_id, run_date, "SUCCESS",
                        start_time=start, end_time=end,
                        rows_loaded=rows,
                        context=result if isinstance(result, dict) else None)
                return result
            except Exception as e:
                end = datetime.now()
                log_run(dag_id, task_id, run_date, "FAILED",
                        start_time=start, end_time=end,
                        error=str(e)[:2000])
                logger.exception("[%s] FAILED", task_id)
                raise
        inner.__name__ = func.__name__
        return inner
    return wrapper
@etl_task("extract")
def extract_task(**context):
    df = pd.read_csv(CSV_PATH)
    df.columns = [c.strip() for c in df.columns]
    tmp = f"/tmp/sales_raw_{context['ds']}.parquet"
    df.to_parquet(tmp, index=False)
    context["ti"].xcom_push(key="raw_path", value=tmp)
    return {"rows_loaded": len(df), "path": tmp}
@etl_task("transform")
def transform_task(**context):
    from etl.transform import transform
    raw_path = context["ti"].xcom_pull(key="raw_path", task_ids="extract")
    df = pd.read_parquet(raw_path)
    df = transform(df)
    tmp = f"/tmp/sales_clean_{context['ds']}.parquet"
    df.to_parquet(tmp, index=False)
    context["ti"].xcom_push(key="clean_path", value=tmp)
    return {"rows_loaded": len(df), "path": tmp}
@etl_task("dq_check")
def dq_check_task(**context):
    clean_path = context["ti"].xcom_pull(key="clean_path", task_ids="transform")
    df = pd.read_parquet(clean_path)
    report = {
        "row_count":         int(len(df)),
        "null_invoice_id":   int(df["invoice_id"].isna().sum()),
        "dup_invoice_id":    int(df["invoice_id"].duplicated().sum()),
        "negative_qty":      int((df["quantity"] <= 0).sum()),
        "tax_mismatch":      int((~df["dq_tax_ok"]).sum()),
        "total_mismatch":    int((~df["dq_total_ok"]).sum()),
        "rating_out_of_rng": int(((df["rating"] < 0) | (df["rating"] > 10)).sum()),
    }
    hook = PostgresHook(postgres_conn_id=PG_CONN_ID)
    hook.run("""
        INSERT INTO dq_report
            (run_date, row_count, null_invoice_id, dup_invoice_id,
             negative_qty, tax_mismatch, total_mismatch, rating_out_of_rng)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, parameters=(
        context["ds"], report["row_count"], report["null_invoice_id"],
        report["dup_invoice_id"], report["negative_qty"],
        report["tax_mismatch"], report["total_mismatch"],
        report["rating_out_of_rng"],
    ), autocommit=True)
    if report["null_invoice_id"] or report["dup_invoice_id"]:
        raise ValueError(f"Data Quality FAILED: {report}")
    return {"rows_loaded": report["row_count"], **report}
@etl_task("load_nds")
def load_nds_task(**context):
    from etl.load_nds import load_nds
    clean_path = context["ti"].xcom_pull(key="clean_path", task_ids="transform")
    df = pd.read_parquet(clean_path)
    engine = create_engine(_pg_uri())
    stats = load_nds(df, engine)
    return {"rows_loaded": stats.get("invoices_loaded", 0), **stats}
@etl_task("load_dds")
def load_dds_task(**context):
    from etl.load_dds import load_dds
    engine = create_engine(_pg_uri())
    stats = load_dds(engine)
    return {"rows_loaded": stats.get("fact_sales", 0), **stats}
@etl_task("build_marts")
def build_marts_task(**context):
    hook = PostgresHook(postgres_conn_id=PG_CONN_ID)
    for mv in ["mv_sales_by_branch",
               "mv_sales_by_product",
               "mv_payment_customer",
               "mv_time_patterns"]:
        hook.run(f"REFRESH MATERIALIZED VIEW {mv};", autocommit=True)
    return {"rows_loaded": 4, "refreshed": True}
with DAG(
    dag_id="sales_etl_pipeline",
    description="ETL sales.csv -> NDS -> DDS -> Marts",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args=default_args,
    tags=["diploma", "etl", "sales", "dwh"],
    max_active_runs=1,
) as dag:
    t_extract   = PythonOperator(task_id="extract",     python_callable=extract_task)
    t_transform = PythonOperator(task_id="transform",   python_callable=transform_task)
    t_dq        = PythonOperator(task_id="dq_check",    python_callable=dq_check_task)
    t_nds       = PythonOperator(task_id="load_nds",    python_callable=load_nds_task)
    t_dds       = PythonOperator(task_id="load_dds",    python_callable=load_dds_task)
    t_marts     = PythonOperator(task_id="build_marts", python_callable=build_marts_task)
    t_extract >> t_transform >> t_dq >> t_nds >> t_dds >> t_marts
