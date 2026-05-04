from pathlib import Path

import pandas as pd
import yaml


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    schema_path = repo_root / "schemas" / "events.schema.yaml"
    input_path = repo_root / "data" / "raw" / "retailrocket" / "events.csv"
    output_dir = repo_root / "data" / "interim"
    output_path = output_dir / "events_standardized.parquet"

    output_dir.mkdir(parents=True, exist_ok=True)

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    raw_columns = schema["raw_source"]["columns"]
    canonical_columns = schema["canonical_event"]["columns"]
    rename_map = schema["canonical_event"]["rename_map"]

    df = pd.read_csv(input_path)

    missing_cols = [col for col in raw_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing expected raw columns: {missing_cols}")

    df = df.rename(columns=rename_map)

    df["event_timestamp"] = pd.to_datetime(df["event_timestamp"], unit="ms", utc=True)
    df["event_date"] = df["event_timestamp"].dt.date

    df["user_id"] = pd.to_numeric(df["user_id"], errors="coerce").astype("Int64")
    df["item_id"] = pd.to_numeric(df["item_id"], errors="coerce").astype("Int64")
    df["transaction_id"] = pd.to_numeric(df["transaction_id"], errors="coerce").astype("Int64")
    df["event_type"] = df["event_type"].astype("string")

    df = df[canonical_columns].sort_values(
        ["event_date", "event_timestamp"]
    ).reset_index(drop=True)

    df.to_parquet(output_path, index=False)

    print(f"Loaded rows: {len(df):,}")
    print(f"Columns: {list(df.columns)}")
    print(f"Saved standardized file to: {output_path}")
    print(df.head())


if __name__ == "__main__":
    main()
