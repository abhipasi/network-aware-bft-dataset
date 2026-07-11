#!/usr/bin/env python3
"""
Generate publication-quality figures for the AWS inter-region RTT dataset.

Outputs:
- Annotated RTT heatmap
- Directed region-pair histograms
- Inter-region RTT boxplot
- Empirical CDF plot
- Region-pair median bar chart
- Geographic topology map (schematic)
- 10-node AWS architecture diagram
- Observation-count chart
- Summary CSV files

Exports figures as PNG, PDF, and SVG.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


REGION_LABELS = {
    "ap-northeast-1": "Tokyo",
    "ap-south-1": "Mumbai",
    "eu-west-1": "Ireland",
    "us-east-1": "Virginia",
    "us-west-2": "Oregon",
}

REGION_ORDER = [
    "ap-northeast-1",
    "ap-south-1",
    "eu-west-1",
    "us-east-1",
    "us-west-2",
]

REGION_COORDS = {
    "Virginia": (-77.0, 38.9),
    "Oregon": (-122.7, 45.5),
    "Ireland": (-6.3, 53.3),
    "Tokyo": (139.7, 35.7),
    "Mumbai": (72.9, 19.1),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("aws_inter_region_rtt_probes.csv.gz"),
        help="Path to the anonymized RTT dataset.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("figures"),
        help="Directory for generated figures and tables.",
    )
    parser.add_argument(
        "--hist-bins",
        type=int,
        default=80,
        help="Histogram bin count.",
    )
    parser.add_argument(
        "--sample-per-pair",
        type=int,
        default=50000,
        help="Maximum rows sampled per directed pair for heavy plots.",
    )
    return parser.parse_args()


def save_all(fig, stem: Path) -> None:
    fig.savefig(stem.with_suffix(".png"), dpi=600, bbox_inches="tight")
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight")


def load_data(path: Path) -> pd.DataFrame:
    required = {
        "timestamp_utc",
        "source_region",
        "source_node",
        "destination_region",
        "destination_node",
        "sequence_number",
        "rtt_microseconds",
        "rtt_milliseconds",
    }

    df = pd.read_csv(path, parse_dates=["timestamp_utc"])
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df["rtt_milliseconds"] = pd.to_numeric(
        df["rtt_milliseconds"], errors="coerce"
    )
    df = df.dropna(subset=[
        "timestamp_utc",
        "source_region",
        "destination_region",
        "rtt_milliseconds",
    ])

    return df


def pair_label(src: str, dst: str) -> str:
    return f"{REGION_LABELS.get(src, src)} → {REGION_LABELS.get(dst, dst)}"


def generate_heatmap(df: pd.DataFrame, out: Path) -> None:
    matrix = (
        df.groupby(["source_region", "destination_region"])["rtt_milliseconds"]
        .median()
        .unstack()
        .reindex(index=REGION_ORDER, columns=REGION_ORDER)
    )

    fig, ax = plt.subplots(figsize=(8.5, 6.8))
    im = ax.imshow(matrix.values, aspect="auto")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Median RTT (ms)")

    labels = [REGION_LABELS[r] for r in REGION_ORDER]
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)

    ax.set_xlabel("Destination region")
    ax.set_ylabel("Source region")
    ax.set_title("AWS Inter-Region Median RTT Heatmap")

    threshold = np.nanmax(matrix.values) / 2
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix.iloc[i, j]
            txt_color = "white" if value > threshold else "black"
            ax.text(
                j, i, f"{value:.2f}",
                ha="center", va="center",
                fontsize=9, color=txt_color
            )

    fig.tight_layout()
    save_all(fig, out / "rtt_heatmap")
    plt.close(fig)
    matrix.round(3).to_csv(out / "rtt_matrix_figure_values.csv")


def generate_histograms(
    df: pd.DataFrame, out: Path, bins: int, sample_per_pair: int
) -> None:
    hist_dir = out / "histograms"
    hist_dir.mkdir(parents=True, exist_ok=True)

    for (src, dst), group in df.groupby(
        ["source_region", "destination_region"]
    ):
        values = group["rtt_milliseconds"].dropna()
        if len(values) > sample_per_pair:
            values = values.sample(sample_per_pair, random_state=42)

        median = values.median()
        p95 = values.quantile(0.95)
        p99 = values.quantile(0.99)

        fig, ax = plt.subplots(figsize=(8.5, 5.4))
        ax.hist(values, bins=bins)
        ax.axvline(median, linestyle="--", linewidth=1.4,
                   label=f"Median = {median:.2f} ms")
        ax.axvline(p95, linestyle=":", linewidth=1.4,
                   label=f"p95 = {p95:.2f} ms")
        ax.axvline(p99, linestyle="-.", linewidth=1.2,
                   label=f"p99 = {p99:.2f} ms")

        ax.set_xlabel("RTT (ms)")
        ax.set_ylabel("Observation count")
        ax.set_title(f"RTT Distribution: {pair_label(src, dst)}")
        ax.legend()
        ax.grid(axis="y", alpha=0.25)
        fig.tight_layout()

        stem = hist_dir / f"{src}_to_{dst}"
        save_all(fig, stem)
        plt.close(fig)


def generate_boxplot(df: pd.DataFrame, out: Path, sample_per_pair: int) -> None:
    sub = df[df["source_region"] != df["destination_region"]].copy()

    samples = []
    labels = []
    for (src, dst), group in sub.groupby(
        ["source_region", "destination_region"]
    ):
        vals = group["rtt_milliseconds"].dropna()
        if len(vals) > sample_per_pair:
            vals = vals.sample(sample_per_pair, random_state=42)
        samples.append(vals.values)
        labels.append(pair_label(src, dst))

    order = np.argsort([np.median(v) for v in samples])
    samples = [samples[i] for i in order]
    labels = [labels[i] for i in order]

    fig, ax = plt.subplots(figsize=(10, 9))
    ax.boxplot(
        samples,
        orientation="horizontal",
        tick_labels=labels,
        showfliers=False,
        whis=(5, 95),
    )
    ax.set_xlabel("RTT (ms)")
    ax.set_ylabel("Directed region pair")
    ax.set_title("Inter-Region RTT Distribution by Directed Pair")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    save_all(fig, out / "inter_region_rtt_boxplot")
    plt.close(fig)


def generate_ecdf(df: pd.DataFrame, out: Path, sample_per_pair: int) -> None:
    fig, ax = plt.subplots(figsize=(9, 6.5))

    key_pairs = [
        ("us-east-1", "us-west-2"),
        ("us-east-1", "eu-west-1"),
        ("ap-south-1", "eu-west-1"),
        ("ap-northeast-1", "us-west-2"),
        ("ap-south-1", "us-west-2"),
    ]

    for src, dst in key_pairs:
        vals = df.loc[
            (df["source_region"] == src)
            & (df["destination_region"] == dst),
            "rtt_milliseconds",
        ].dropna()

        if len(vals) > sample_per_pair:
            vals = vals.sample(sample_per_pair, random_state=42)

        x = np.sort(vals.values)
        y = np.arange(1, len(x) + 1) / len(x)
        ax.plot(x, y, label=pair_label(src, dst), linewidth=1.5)

    ax.set_xlabel("RTT (ms)")
    ax.set_ylabel("Empirical cumulative probability")
    ax.set_title("Empirical CDF of Selected Inter-Region RTT Pairs")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    save_all(fig, out / "rtt_ecdf_selected_pairs")
    plt.close(fig)


def generate_median_bars(df: pd.DataFrame, out: Path) -> None:
    med = (
        df[df["source_region"] != df["destination_region"]]
        .groupby(["source_region", "destination_region"])["rtt_milliseconds"]
        .median()
        .reset_index()
    )
    med["pair"] = med.apply(
        lambda r: pair_label(r["source_region"], r["destination_region"]),
        axis=1,
    )
    med = med.sort_values("rtt_milliseconds")

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(med["pair"], med["rtt_milliseconds"])
    ax.set_xlabel("Median RTT (ms)")
    ax.set_ylabel("Directed region pair")
    ax.set_title("Median Inter-Region RTT by Directed Pair")
    ax.grid(axis="x", alpha=0.25)

    for i, value in enumerate(med["rtt_milliseconds"]):
        ax.text(value + 2, i, f"{value:.2f}", va="center", fontsize=8)

    fig.tight_layout()
    save_all(fig, out / "inter_region_median_rtt")
    plt.close(fig)
    med.to_csv(out / "inter_region_median_rtt.csv", index=False)


def generate_counts(df: pd.DataFrame, out: Path) -> None:
    counts = (
        df.groupby("source_region")
        .size()
        .reindex(REGION_ORDER)
    )

    labels = [REGION_LABELS[r] for r in REGION_ORDER]

    fig, ax = plt.subplots(figsize=(8, 5.2))
    ax.bar(labels, counts.values)
    ax.set_ylabel("Observation count")
    ax.set_title("RTT Observations by Source Region")
    ax.ticklabel_format(style="plain", axis="y")
    ax.grid(axis="y", alpha=0.25)

    for i, value in enumerate(counts.values):
        ax.text(i, value, f"{int(value):,}", ha="center", va="bottom", fontsize=9)

    fig.tight_layout()
    save_all(fig, out / "observation_counts_by_region")
    plt.close(fig)


def generate_topology(out: Path) -> None:
    positions = {
        "Virginia": (0.15, 0.65),
        "Oregon": (0.15, 0.30),
        "Ireland": (0.50, 0.78),
        "Tokyo": (0.85, 0.65),
        "Mumbai": (0.85, 0.30),
    }

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis("off")

    names = list(positions.keys())
    for i, a in enumerate(names):
        x1, y1 = positions[a]
        for b in names[i + 1:]:
            x2, y2 = positions[b]
            ax.plot([x1, x2], [y1, y2], linewidth=0.8, alpha=0.45)

    for name, (x, y) in positions.items():
        ax.scatter([x], [y], s=1500)
        ax.text(
            x, y,
            f"{name}\n2 nodes",
            ha="center", va="center",
            fontsize=11,
        )

    ax.text(
        0.5, 0.08,
        "5 AWS regions • 2 nodes per region • 10 nodes total",
        ha="center", fontsize=12, fontweight="bold"
    )
    ax.set_title("Geo-Distributed AWS Measurement Architecture", fontsize=15)
    fig.tight_layout()
    save_all(fig, out / "network_topology")
    plt.close(fig)


def generate_world_map(out: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 5.8))

    ax.set_xlim(-180, 180)
    ax.set_ylim(-60, 85)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Geographic Placement of AWS Measurement Regions")
    ax.grid(alpha=0.2)

    # Very light schematic continental bands to preserve portability.
    ax.axhspan(-60, 85, alpha=0.03)
    ax.axvline(0, linewidth=0.5, alpha=0.3)
    ax.axhline(0, linewidth=0.5, alpha=0.3)

    for name, (lon, lat) in REGION_COORDS.items():
        ax.scatter([lon], [lat], s=180)
        ax.text(lon + 4, lat + 2, f"{name}\n2 nodes", fontsize=9)

    fig.tight_layout()
    save_all(fig, out / "regional_topology_map")
    plt.close(fig)


def generate_summary(df: pd.DataFrame, out: Path) -> None:
    summary = (
        df.groupby(["source_region", "destination_region"])["rtt_milliseconds"]
        .agg(
            count="count",
            mean_ms="mean",
            median_ms="median",
            std_ms="std",
            min_ms="min",
            p95_ms=lambda s: s.quantile(0.95),
            p99_ms=lambda s: s.quantile(0.99),
            max_ms="max",
        )
        .reset_index()
    )
    numeric = summary.select_dtypes(include="number").columns
    summary[numeric] = summary[numeric].round(3)
    summary.to_csv(out / "publication_summary_statistics.csv", index=False)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    df = load_data(args.input)

    generate_heatmap(df, args.output_dir)
    generate_histograms(df, args.output_dir, args.hist_bins, args.sample_per_pair)
    generate_boxplot(df, args.output_dir, args.sample_per_pair)
    generate_ecdf(df, args.output_dir, args.sample_per_pair)
    generate_median_bars(df, args.output_dir)
    generate_counts(df, args.output_dir)
    generate_topology(args.output_dir)
    generate_world_map(args.output_dir)
    generate_summary(df, args.output_dir)

    print("Publication-quality figure package generated in:")
    print(args.output_dir)
    print("Formats: PNG, PDF, SVG")


if __name__ == "__main__":
    main()
