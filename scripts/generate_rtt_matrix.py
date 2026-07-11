#!/usr/bin/env python3
"""Generate RTT matrix, summary statistics, and stationarity tables."""

from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

def q95(s): return s.quantile(0.95)
def q99(s): return s.quantile(0.99)

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path,
                   default=Path("data/ieee_dataport/aws_inter_region_rtt_probes.csv.gz"))
    p.add_argument("--output-dir", type=Path, default=Path("data/ieee_dataport"))
    p.add_argument("--window", default="30min")
    args = p.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(args.input, parse_dates=["timestamp_utc"])

    required = {"timestamp_utc", "source_region", "destination_region", "rtt_milliseconds"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    matrix = (
        df.groupby(["source_region", "destination_region"])["rtt_milliseconds"]
        .median().unstack().sort_index().sort_index(axis=1).round(3)
    )
    matrix.to_csv(args.output_dir / "rtt_matrix.csv")

    summary = (
        df.groupby(["source_region", "destination_region"])["rtt_milliseconds"]
        .agg(
            count="count",
            mean_ms="mean",
            median_ms="median",
            std_ms="std",
            min_ms="min",
            p95_ms=q95,
            p99_ms=q99,
            max_ms="max",
        )
        .reset_index()
    )
    numeric = summary.select_dtypes("number").columns
    summary[numeric] = summary[numeric].round(3)
    summary.to_csv(args.output_dir / "rtt_summary.csv", index=False)

    stationarity = (
        df.set_index("timestamp_utc")
        .groupby([
            pd.Grouper(freq=args.window),
            "source_region",
            "destination_region",
        ])["rtt_milliseconds"]
        .agg(count="count", mean_ms="mean", median_ms="median",
             std_ms="std", min_ms="min", max_ms="max")
        .reset_index()
    )
    numeric = stationarity.select_dtypes("number").columns
    stationarity[numeric] = stationarity[numeric].round(3)
    stationarity.to_csv(args.output_dir / "rtt_stationarity.csv", index=False)

    print("Generated:")
    print(args.output_dir / "rtt_matrix.csv")
    print(args.output_dir / "rtt_summary.csv")
    print(args.output_dir / "rtt_stationarity.csv")

if __name__ == "__main__":
    main()
