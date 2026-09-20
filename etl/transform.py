"""Очистка и обогащение данных."""
import pandas as pd
RENAME = {
    "Invoice ID": "invoice_id", "Branch": "branch_code",
    "City": "city", "Customer type": "customer_type",
    "Gender": "gender", "Product line": "product_line",
    "Unit price": "unit_price", "Quantity": "quantity",
    "Tax 5%": "tax_5pct", "Total": "total",
    "Date": "sale_date", "Time": "sale_time",
    "Payment": "payment", "cogs": "cogs",
    "gross margin percentage": "gross_margin_pct",
    "gross income": "gross_income", "Rating": "rating",
}
def transform(df: pd.DataFrame) -> pd.DataFrame:
    df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y").dt.date
    df["Time"] = pd.to_datetime(df["Time"], format="%H:%M").dt.time
    df = df.rename(columns=RENAME)
    df = df.drop_duplicates(subset=["invoice_id"])
    df["calc_tax"]   = (df["cogs"] * 0.05).round(4)
    df["calc_total"] = (df["cogs"] + df["tax_5pct"]).round(4)
    df["dq_tax_ok"]  = (df["tax_5pct"] - df["calc_tax"]).abs() < 0.01
    df["dq_total_ok"]= (df["total"] - df["calc_total"]).abs() < 0.01
    print(f"[TRANSFORM] Готово {len(df)} строк")
    return df
