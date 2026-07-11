#!/usr/bin/env python3
"""Validate the IEEE DataPort RTT dataset."""

from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

EXPECTED_ROWS = 3_090_940
EXPECTED_REGIONS = {
    "us-east-1", "us-west-2", "eu-west-1",
    "ap-northeast-1", "ap-south-1"
}
REQUIRED = [
    "timestamp_utc", "source_region", "source_node",
    "destination_region", "destination_node",
    "sequence_number", "rtt_microseconds", "rtt_milliseconds"
]

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path,
                   default=Path("data/ieee_dataport/aws_inter_region_rtt_probes.csv.gz"))
    args = p.parse_args()

    df = pd.read_csv(args.input)
    failures = []

    missing_cols = [c for c in REQUIRED if c not in df.columns]
    if missing_cols:
        failures.append(f"Missing columns: {missing_cols}")

    if len(df) != EXPECTED_ROWS:
        failures.append(f"Row count is {len(df):,}; expected {EXPECTED_ROWS:,}")

    if not missing_cols:
        ts = pd.to_datetime(df["timestamp_utc"], utc=True, errors="coerce")
        if ts.isna().any():
            failures.append(f"Invalid timestamps: {ts.isna().sum():,}")

        for col in REQUIRED:
            n = df[col].isna().sum()
            if n:
                failures.append(f"Missing values in {col}: {n:,}")

        source_regions = set(df["source_region"].dropna().unique())
        dest_regions = set(df["destination_region"].dropna().unique())
        if source_regions != EXPECTED_REGIONS:
            failures.append(f"Unexpected source regions: {source_regions}")
        if dest_regions != EXPECTED_REGIONS:
            failures.append(f"Unexpected destination regions: {dest_regions}")

        if (df["rtt_microseconds"] < 0).any():
            failures.append("Negative rtt_microseconds values found")
        if (df["rtt_milliseconds"] < 0).any():
            failures.append("Negative rtt_milliseconds values found")

        conversion_error = (
            df["rtt_milliseconds"] - df["rtt_microseconds"] / 1000.0
        ).abs().max()
        if conversion_error > 1e-9:
            failures.append(f"RTT conversion mismatch; maximum error={conversion_error}")

        print("Dataset summary")
        print(f"Rows:              {len(df):,}")
        print(f"Columns:           {len(df.columns)}")
        print(f"Source regions:    {df['source_region'].nunique()}")
        print(f"Destination regions:{df['destination_region'].nunique()}")
        print(f"Source nodes:      {df['source_node'].nunique()}")
        print(f"Destination nodes: {df['destination_node'].nunique()}")
        print(f"Start:             {ts.min()}")
        print(f"End:               {ts.max()}")
        print(f"Exact duplicates:  {df.duplicated().sum():,}")

    if failures:
        print("\nVALIDATION FAILED")
        for item in failures:
            print(" -", item)
        raise SystemExit(1)

    print("\nVALIDATION PASSED")

if __name__ == "__main__":
    main()
