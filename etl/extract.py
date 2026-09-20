"""Извлечение данных из CSV."""
import pandas as pd
def extract_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    print(f"[EXTRACT] Загружено {len(df)} строк из {path}")
    return df
