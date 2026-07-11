#!/usr/bin/env python3
"""Combine and anonymize AWS RTT probe logs."""

from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import pandas as pd

EXPECTED_FILES = 10
EXPECTED_ROWS = 3_090_940
REQUIRED = {"ts_iso", "self_ip", "peer_ip", "peer_region", "seq", "rtt_us"}

def anon(value: object) -> str:
    return "node_" + hashlib.sha256(str(value).encode()).hexdigest()[:12]

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    p.add_argument("--output", type=Path,
                   default=Path("data/ieee_dataport/aws_inter_region_rtt_probes.csv.gz"))
    p.add_argument("--allow-row-count-mismatch", action="store_true")
    args = p.parse_args()

    files = sorted(args.raw_dir.glob("*/*/probes.csv"))
    if not files:
        raise FileNotFoundError(f"No probes.csv files found under {args.raw_dir}")
    if len(files) != EXPECTED_FILES:
        print(f"WARNING: expected {EXPECTED_FILES} files, found {len(files)}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        args.output.unlink()

    total = 0
    first = True
    global_start = None
    global_end = None

    for file in files:
        source_region = file.parent.parent.name
        source_public_ip = file.parent.name
        df = pd.read_csv(file)

        missing = REQUIRED - set(df.columns)
        if missing:
            raise ValueError(f"{file}: missing columns {sorted(missing)}")

        ts = pd.to_datetime(df["ts_iso"], utc=True, errors="coerce")
        rtt = pd.to_numeric(df["rtt_us"], errors="coerce")

        if ts.isna().any():
            raise ValueError(f"{file}: invalid timestamps found")
        if rtt.isna().any():
            raise ValueError(f"{file}: invalid RTT values found")
        if (rtt < 0).any():
            raise ValueError(f"{file}: negative RTT values found")

        file_start, file_end = ts.min(), ts.max()
        global_start = file_start if global_start is None else min(global_start, file_start)
        global_end = file_end if global_end is None else max(global_end, file_end)

        clean = pd.DataFrame({
            "timestamp_utc": df["ts_iso"],
            "source_region": source_region,
            "source_node": anon(source_public_ip),
            "destination_region": df["peer_region"],
            "destination_node": df["peer_ip"].map(anon),
            "sequence_number": df["seq"].astype("int64"),
            "rtt_microseconds": rtt.astype("int64"),
            "rtt_milliseconds": rtt / 1000.0,
        })

        clean.to_csv(
            args.output,
            mode="wt" if first else "at",
            header=first,
            index=False,
            compression="gzip",
        )
        first = False
        total += len(clean)
        print(f"{len(clean):,} rows  {file}")

    if total != EXPECTED_ROWS and not args.allow_row_count_mismatch:
        raise RuntimeError(
            f"Expected {EXPECTED_ROWS:,} rows but wrote {total:,}. "
            "Use --allow-row-count-mismatch only if intentional."
        )

    print("\nCombined dataset created")
    print(f"Files:    {len(files)}")
    print(f"Rows:     {total:,}")
    print(f"Start:    {global_start}")
    print(f"End:      {global_end}")
    print(f"Duration: {global_end - global_start}")
    print(f"Output:   {args.output}")

if __name__ == "__main__":
    main()
