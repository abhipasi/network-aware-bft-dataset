#!/usr/bin/env python3
"""Reproduce Experiment E1 tables and figures."""

from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

LABELS = {
    "us-east-1": "Virginia",
    "us-west-2": "Oregon",
    "eu-west-1": "Ireland",
    "ap-northeast-1": "Tokyo",
    "ap-south-1": "Mumbai",
}

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path,
                   default=Path("data/ieee_dataport/aws_inter_region_rtt_probes.csv.gz"))
    p.add_argument("--output-dir", type=Path,
                   default=Path("data/ieee_dataport/figures"))
    args = p.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input, parse_dates=["timestamp_utc"])

    matrix = (
        df.groupby(["source_region", "destination_region"])["rtt_milliseconds"]
        .median().unstack().sort_index().sort_index(axis=1)
    )
    matrix.to_csv(args.output_dir / "e1_rtt_matrix.csv")

    fig, ax = plt.subplots(figsize=(8, 6))
    image = ax.imshow(matrix.values, aspect="auto")
    fig.colorbar(image, ax=ax, label="Median RTT (ms)")
    ax.set_xticks(range(len(matrix.columns)))
    ax.set_yticks(range(len(matrix.index)))
    ax.set_xticklabels([LABELS.get(x, x) for x in matrix.columns], rotation=45, ha="right")
    ax.set_yticklabels([LABELS.get(x, x) for x in matrix.index])
    ax.set_xlabel("Destination region")
    ax.set_ylabel("Source region")
    ax.set_title("AWS Inter-Region Median RTT Matrix")

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, f"{matrix.iloc[i, j]:.2f}", ha="center", va="center")

    fig.tight_layout()
    fig.savefig(args.output_dir / "rtt_heatmap.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # Region-pair median bar chart (excluding same-region values)
    pairs = (
        df[df["source_region"] != df["destination_region"]]
        .groupby(["source_region", "destination_region"])["rtt_milliseconds"]
        .median()
        .reset_index()
    )
    pairs["pair"] = pairs["source_region"] + " → " + pairs["destination_region"]
    pairs = pairs.sort_values("rtt_milliseconds")

    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(pairs["pair"], pairs["rtt_milliseconds"])
    ax.set_xlabel("Median RTT (ms)")
    ax.set_ylabel("Region pair")
    ax.set_title("Inter-Region RTT by Directed Region Pair")
    fig.tight_layout()
    fig.savefig(args.output_dir / "inter_region_rtt_bars.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # RTT distribution for every region pair in one CSV summary
    summary = (
        df.groupby(["source_region", "destination_region"])["rtt_milliseconds"]
        .describe(percentiles=[0.50, 0.90, 0.95, 0.99])
        .reset_index()
    )
    summary.to_csv(args.output_dir / "e1_distribution_summary.csv", index=False)

    print("Experiment E1 reproduced in:", args.output_dir)
    for name in [
        "e1_rtt_matrix.csv",
        "rtt_heatmap.png",
        "inter_region_rtt_bars.png",
        "e1_distribution_summary.csv",
    ]:
        print(" -", args.output_dir / name)

if __name__ == "__main__":
    main()
