# Table 2 - full grid

English-only pipeline: docs, CLI (`--help`), console output, and generated `summary/` files are in English. Unrelated folders (e.g. `projects/`) are not part of this workflow.

## Layout

```
.
├── README.md
├── table2_dataset.xlsx          # Main data at repo root (long table on sheet raw_data)
├── analysis/
│   ├── requirements.txt
│   └── build_table2_paper_grid.py
└── summary/                     # Outputs: table2_paper_full_grid.* and wilcoxon_*.csv
```

## Setup

```powershell
cd "path\to\Scratch Feedback"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r analysis/requirements.txt
```

## Generate the table

From the repo root:

```powershell
python analysis/build_table2_paper_grid.py
```

Outputs: `summary/table2_paper_full_grid.md`, `summary/table2_paper_full_grid.csv`, and `summary/wilcoxon_table2_all_cells.csv` (Holm-adjusted *p*-values).