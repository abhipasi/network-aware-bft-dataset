# AWS Inter-Region RTT Measurements for Network-Aware BFT Consensus Evaluation

## Dataset Information

| Field | Value |
|---|---|
| Dataset title | AWS Inter-Region RTT Measurements for Network-Aware BFT Consensus Evaluation |
| Version | 1.0 |
| Creator | Abhijeet A. Pasi |
| Affiliation | K. J. Somaiya School of Engineering (Formerly K J Somaiya College of Engineering), Somaiya Vidyavihar University, Mumbai, India |
| Corresponding email | abhijeet.pasi@somaiya.edu |
| Collection dates | 8–9 July 2026 |
| Collection period | 2026-07-08 16:57:59.676 UTC to 2026-07-09 01:42:08.981 UTC |
| Observation duration | 8 hours, 44 minutes, 9.305 seconds |
| AWS regions | 5 |
| Measurement nodes | 10 |
| Nodes per region | 2 |
| RTT observations | 3,090,940 |
| Primary data format | GZIP-compressed CSV |
| RTT units | Microseconds and milliseconds |
| License | MIT License |
| DataPort DOI | To be added after publication |
| Related paper DOI | To be added when available |

## 1. Overview

This dataset contains **3,090,940 round-trip-time (RTT) measurements** collected from ten Amazon Web Services (AWS) nodes distributed across five geographic regions:

- `us-east-1`
- `us-west-2`
- `eu-west-1`
- `ap-northeast-1`
- `ap-south-1`

Two measurement nodes were deployed in each region. Every node periodically measured RTT to participating intra-region and inter-region peers. The resulting observations support the evaluation of geo-distributed Byzantine fault-tolerant consensus, network-aware committee placement, adaptive timeout configuration, regional concentration, and network-degradation resilience.

The publication dataset uses stable anonymous node identifiers. Public and private IP addresses from the original measurement environment are not included.

## 2. Research Purpose

The dataset was collected to support the following research objectives:

1. Measure real inter-region and intra-region communication delays across geographically distributed AWS locations.
2. construct an empirical regional RTT matrix for network-aware BFT simulations.
3. Evaluate the effect of validator or committee placement on quorum communication delay.
4. Support adaptive timeout selection using observed network conditions.
5. Study consensus behaviour under regional latency degradation, jitter, and partial outages.
6. Enable reproducible evaluation of geo-distributed blockchain consensus mechanisms.

## 3. Dataset Contents

```text
FW_Network_Evaluation_Dataset/
├── README.md
├── LICENSE.txt
├── CITATION.cff
├── data_dictionary.csv
├── requirements.txt
├── SHA256SUMS.txt
├── aws_inter_region_rtt_probes.csv.gz
├── rtt_matrix.csv
├── rtt_summary.csv
├── rtt_stationarity.csv
├── scripts/
│   ├── combine_and_anonymize.py
│   ├── generate_rtt_matrix.py
│   ├── verify_dataset.py
│   └── reproduce_e1.py
└── figures/
    ├── rtt_heatmap.png
    ├── rtt_histograms.png
    └── network_topology.png
```

### 3.1 Primary dataset

`aws_inter_region_rtt_probes.csv.gz` contains the complete anonymized measurement dataset.

### 3.2 Derived datasets

- `rtt_matrix.csv`: regional median RTT matrix in milliseconds.
- `rtt_summary.csv`: descriptive statistics for each source–destination region pair.
- `rtt_stationarity.csv`: time-window-based RTT stability statistics.
- `data_dictionary.csv`: definitions, types, units, and examples for all columns.

### 3.3 Reproduction scripts

- `combine_and_anonymize.py`: combines the ten original probe files and replaces infrastructure IP addresses with stable anonymous node identifiers.
- `generate_rtt_matrix.py`: creates the regional RTT matrix, summary statistics, and stationarity table.
- `verify_dataset.py`: checks row count, schema, missing values, duplicate rows, timestamp range, RTT validity, and region coverage.
- `reproduce_e1.py`: recreates the main tables and figures for Experiment E1.

## 4. Measurement Configuration

| Parameter | Value |
|---|---:|
| Number of AWS regions | 5 |
| Nodes per region | 2 |
| Total nodes | 10 |
| Total observations | 3,090,940 |
| Collection start | 2026-07-08 16:57:59.676 UTC |
| Collection end | 2026-07-09 01:42:08.981 UTC |
| Overall duration | 8:44:09.305 |
| Original RTT unit | Microseconds |
| Publication RTT units | Microseconds and milliseconds |
| Timestamp standard | ISO 8601 UTC |

The overall duration is calculated from the earliest timestamp across all node logs to the latest timestamp across all node logs. Individual node logs may have slightly different start and end times.

## 5. Regional Deployment

| AWS region | Geographic label used in the study | Nodes |
|---|---|---:|
| `us-east-1` | Virginia, United States | 2 |
| `us-west-2` | Oregon, United States | 2 |
| `eu-west-1` | Ireland | 2 |
| `ap-northeast-1` | Tokyo, Japan | 2 |
| `ap-south-1` | Mumbai, India | 2 |

Geographic labels are provided only for readability. AWS region identifiers are the authoritative location fields in the dataset.

## 6. Data Schema

The primary dataset contains eight columns.

| Column | Type | Unit | Description |
|---|---|---|---|
| `timestamp_utc` | datetime string | UTC | ISO 8601 timestamp at which the RTT observation was recorded. |
| `source_region` | string | — | AWS region containing the node that generated the measurement. |
| `source_node` | string | — | Stable anonymized identifier of the source node. |
| `destination_region` | string | — | AWS region containing the destination peer. |
| `destination_node` | string | — | Stable anonymized identifier of the destination node. |
| `sequence_number` | integer | — | Probe sequence number assigned by the measurement process. |
| `rtt_microseconds` | integer | µs | Original measured RTT in microseconds. |
| `rtt_milliseconds` | floating point | ms | RTT converted from microseconds to milliseconds. |

The conversion is:

```math
\mathrm{RTT}_{\mathrm{ms}}
=
\frac{\mathrm{RTT}_{\mu\mathrm{s}}}{1000}
```

The `rtt_microseconds` field contains the original measured values, whereas `rtt_milliseconds` is a derived field provided for convenient analysis and visualization.


## 7. Anonymization

The original node logs contained public peer IP addresses and private AWS VPC addresses. These fields were removed from the publication dataset.

Stable anonymous identifiers were created using a one-way hash-based mapping:

```text
node_<12-character hash>
```

The same infrastructure node therefore retains the same anonymous identifier throughout the dataset, allowing node-level analysis without exposing IP addresses.

The following original fields are not published:

- `self_ip`
- `peer_ip`
- source public IP encoded in the raw folder name

## 8. Data Preparation

The publication dataset was prepared using the following workflow:

1. Locate the ten original `probes.csv` files.
2. Validate the required raw columns.
3. Derive `source_region` from the parent folder.
4. read `destination_region` from `peer_region`.
5. Convert timestamps to UTC-compatible ISO 8601 values.
6. Validate that RTT measurements are numeric and non-negative.
7. Replace source and destination IP addresses with stable anonymous node identifiers.
8. Convert RTT from microseconds to milliseconds.
9. Concatenate all records into one compressed CSV file.
10. Generate the regional RTT matrix, pairwise summaries, and stationarity results.
11. Generate SHA-256 checksums for integrity verification.

No synthetic RTT records were added to the primary dataset.

## 9. Data Quality and Validation

The following checks should pass for version 1.0:

| Validation item | Expected result |
|---|---|
| Probe files processed | 10 |
| Total records | 3,090,940 |
| AWS source regions | 5 |
| AWS destination regions | 5 |
| Anonymous source nodes | 10 |
| Anonymous destination nodes | 10 |
| Missing mandatory values | 0 expected |
| Negative RTT values | 0 expected |
| Invalid timestamps | 0 expected |
| Collection start | 2026-07-08 16:57:59.676 UTC |
| Collection end | 2026-07-09 01:42:08.981 UTC |

The ten original log sizes were:

| Source region | Original node log | Records |
|---|---|---:|
| `ap-northeast-1` | Node 1 | 309,487 |
| `ap-northeast-1` | Node 2 | 309,555 |
| `ap-south-1` | Node 1 | 309,602 |
| `ap-south-1` | Node 2 | 309,624 |
| `eu-west-1` | Node 1 | 309,329 |
| `eu-west-1` | Node 2 | 309,166 |
| `us-east-1` | Node 1 | 308,071 |
| `us-east-1` | Node 2 | 308,291 |
| `us-west-2` | Node 1 | 308,748 |
| `us-west-2` | Node 2 | 309,067 |
| **Total** | **10 logs** | **3,090,940** |

## 10. Derived RTT Matrix

The regional RTT matrix is generated by grouping observations by `source_region` and `destination_region` and calculating the median RTT in milliseconds.

The version used in the associated evaluation is:

| Source \ Destination | `ap-northeast-1` | `ap-south-1` | `eu-west-1` | `us-east-1` | `us-west-2` |
|---|---:|---:|---:|---:|---:|
| `ap-northeast-1` | 0.71 | 126.69 | 202.51 | 149.09 | 98.15 |
| `ap-south-1` | 126.69 | 0.11 | 119.68 | 196.48 | 230.34 |
| `eu-west-1` | 202.51 | 119.68 | 0.35 | 68.36 | 116.92 |
| `us-east-1` | 149.09 | 196.48 | 68.36 | 0.21 | 61.05 |
| `us-west-2` | 98.15 | 230.34 | 116.92 | 61.05 | 0.14 |

Values are in milliseconds.

## 11. Software Requirements

Recommended environment:

- Python 3.10 or later
- pandas
- NumPy
- Matplotlib

Install dependencies with:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

A minimal `requirements.txt` is:

```text
pandas>=2.2
numpy>=2.0
matplotlib>=3.8
```

## 12. Reproducing the Dataset

Run the commands from the project root containing `data/raw`.

### 12.1 Combine and anonymize the original logs

```bash
python3 FW_Network_Evaluation_Dataset/scripts/combine_and_anonymize.py \
  --raw-dir data/raw \
  --output-dir FW_Network_Evaluation_Dataset
```

Expected result:

```text
Files processed: 10
Rows written: 3,090,940
```

### 12.2 Generate derived RTT files

```bash
python3 FW_Network_Evaluation_Dataset/scripts/generate_rtt_matrix.py \
  --input FW_Network_Evaluation_Dataset/aws_inter_region_rtt_probes.csv.gz \
  --output-dir FW_Network_Evaluation_Dataset
```

This creates:

```text
rtt_matrix.csv
rtt_summary.csv
rtt_stationarity.csv
```

### 12.3 Verify the publication dataset

```bash
python3 FW_Network_Evaluation_Dataset/scripts/verify_dataset.py \
  --input FW_Network_Evaluation_Dataset/aws_inter_region_rtt_probes.csv.gz
```

### 12.4 Reproduce Experiment E1

```bash
python3 FW_Network_Evaluation_Dataset/scripts/reproduce_e1.py \
  --input FW_Network_Evaluation_Dataset/aws_inter_region_rtt_probes.csv.gz \
  --output-dir FW_Network_Evaluation_Dataset/figures
```

## 13. Reading the Dataset

Because the primary file is GZIP-compressed, pandas can read it directly:

```python
import pandas as pd

df = pd.read_csv(
    "aws_inter_region_rtt_probes.csv.gz",
    parse_dates=["timestamp_utc"],
)

print(df.shape)
print(df.head())
print(df["rtt_milliseconds"].describe())
```

Load only selected columns when memory is limited:

```python
import pandas as pd

columns = [
    "timestamp_utc",
    "source_region",
    "destination_region",
    "rtt_milliseconds",
]

df = pd.read_csv(
    "aws_inter_region_rtt_probes.csv.gz",
    usecols=columns,
    parse_dates=["timestamp_utc"],
)
```

## 14. Integrity Verification

The package includes SHA-256 checksums in `SHA256SUMS.txt`.

On Linux, macOS, or WSL:

```bash
sha256sum -c SHA256SUMS.txt
```

To regenerate the checksum file:

```bash
find . -type f ! -name "SHA256SUMS.txt" -print0 \
  | sort -z \
  | xargs -0 sha256sum > SHA256SUMS.txt
```

## 15. Limitations

1. The measurement window covers approximately 8 hours and 44 minutes and does not represent long-term seasonal or multi-day Internet behaviour.
2. The dataset contains measurements from two nodes per AWS region; it does not capture every availability zone or instance type.
3. RTT values reflect the network conditions observed during the stated collection period.
4. The dataset focuses on RTT and does not directly measure throughput, packet loss, route changes, or application-level processing delays.
5. Anonymous node identifiers do not preserve public IP information.
6. Intra-region RTT measurements should not be interpreted as universal AWS regional latency.
7. The regional median matrix summarizes the raw observations and therefore does not preserve the full tail-latency distribution.

## 16. Recommended Use

The dataset may be used for:

- Geo-distributed consensus simulation
- BFT timeout calibration
- Network-aware validator placement
- Quorum-delay estimation
- Regional latency comparison
- Tail-latency analysis
- RTT stationarity analysis
- Network resilience studies
- Reproducibility studies associated with the related research paper

Researchers should use the primary RTT observations rather than only the regional matrix when modelling jitter, tail latency, or temporal changes.

## 17. License

The dataset and supporting scripts are released under the terms provided in `LICENSE.txt`.

Users may use, modify, and redistribute the material subject to the conditions of the selected license. Users should cite the dataset and associated publication when using the material in academic work.

## 18. Citation

After the IEEE DataPort DOI is assigned, replace the placeholder below.

```text
A. A. Pasi, "AWS Inter-Region RTT Measurements for Network-Aware BFT Consensus Evaluation," IEEE DataPort, version 1.0, 2026, doi: [DATASET DOI].
```

BibTeX template:

```bibtex
@dataset{pasi2026awsrtt,
  author    = {Abhijeet A. Pasi},
  title     = {AWS Inter-Region RTT Measurements for Network-Aware BFT Consensus Evaluation},
  year      = {2026},
  publisher = {IEEE DataPort},
  version   = {1.0},
  doi       = {[DATASET DOI]}
}
```

## 19. Related Publication

Add the related paper after submission or publication:

```text
Title: [RELATED PAPER TITLE]
Authors: [AUTHOR LIST]
Journal: [JOURNAL NAME]
Year: [YEAR]
DOI: [PAPER DOI]
```

## 20. Contact

For questions regarding the dataset, methodology, or reproduction scripts, contact:

**Abhijeet A. Pasi**  
K. J. Somaiya School of Engineering  
Somaiya Vidyavihar University  
Mumbai, India  
Email: abhijeet.pasi@somaiya.edu

## 21. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | July 2026 | Initial release containing 3,090,940 anonymized RTT observations and derived regional statistics. |
