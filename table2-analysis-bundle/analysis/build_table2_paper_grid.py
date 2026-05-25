"""
Table 2: null, per-LLM rows, and Mean - 95% bootstrap CIs in every cell, Wilcoxon stars vs null
(and Holm-adjusted p-values in the CSV).

Reads `table2_dataset.xlsx`, sheet `raw_data` at project root by default (--xlsx / --sheet override).

Run: python analysis/build_table2_paper_grid.py
"""
from __future__ import annotations

import argparse
import csv
import locale
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

# Favor UTF-8 and C locale for predictable, English-oriented formatting from libs (best effort on Windows).
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

DEFAULT_TABLE2_WORKBOOK = "table2_dataset.xlsx"
DEFAULT_TABLE2_SHEET = "raw_data"

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_XLSX = ROOT / DEFAULT_TABLE2_WORKBOOK

COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "condition": ("condition", "cond", "setting"),
    "prompt_id": ("prompt_id", "promptid"),
    "backend": ("backend", "model", "llm", "engine"),
    "executability": ("executability", "executable", "exec"),
    "intent_align": ("intent align", "intent_align", "intentalignment"),
    "script_quality": ("script quality", "script_quality", "scriptquality"),
}

BACKEND_ORDER = [
    "qwen4b",
    "llama8b",
    "deepseek16b",
    "claude",
    "qwenmax",
    "gpt-4omini",
]

METRIC_KEYS = ("executability", "intent_align", "script_quality")


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    lower_map = {str(c).lower().strip(): c for c in df.columns}
    rename: dict[str, str] = {}
    for canon, aliases in COLUMN_ALIASES.items():
        for a in aliases:
            key = a.lower().strip()
            if key in lower_map:
                orig = lower_map[key]
                rename[orig] = canon
                break
    return df.rename(columns=rename)


def load_table2_dataset(
    path: Path,
    sheet: str = DEFAULT_TABLE2_SHEET,
) -> pd.DataFrame:
    """Blank condition = null; `{model} abl.` / `{model} full` → ablation/full plus backend."""
    df = pd.read_excel(path, sheet_name=sheet)
    df = _normalize_columns(df)
    required = ["condition", "prompt_id", "executability", "intent_align", "script_quality"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Long table missing columns: {missing}. Got: {list(df.columns)}")

    cond_out: list[str] = []
    backend_out: list[Any] = []
    for c in df["condition"]:
        if pd.isna(c) or (isinstance(c, str) and str(c).strip() == ""):
            cond_out.append("null")
            backend_out.append(None)
            continue
        s = str(c).strip()
        if s.endswith(" abl."):
            cond_out.append("ablation")
            backend_out.append(s[: -len(" abl.")].strip())
        elif s.endswith(" full"):
            cond_out.append("full")
            backend_out.append(s[: -len(" full")].strip())
        else:
            raise ValueError(
                f"Unparseable condition {s!r}; expected blank, '... abl.', or '... full'"
            )
    df["_cond"] = cond_out
    df["backend"] = backend_out
    for col in ("executability", "intent_align", "script_quality"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ("executability", "intent_align", "script_quality"):
        if df[col].isna().any():
            raise ValueError(f"{col}: non-numeric or missing values.")
    return df


def prompt_level_means(df: pd.DataFrame) -> dict[str, Any]:
    agg = df.groupby(["prompt_id", "_cond"], as_index=False)[
        ["executability", "intent_align", "script_quality"]
    ].mean()
    prompt_ids = sorted(df["prompt_id"].unique().tolist())
    wide: dict[str, Any] = {"prompt_id": prompt_ids}
    for metric in ("executability", "intent_align", "script_quality"):
        sub = agg.pivot(index="prompt_id", columns="_cond", values=metric)
        for cond in ("null", "ablation", "full"):
            if cond not in sub.columns:
                raise ValueError(
                    f"After aggregation, condition {cond} is missing. Check that all settings are present."
                )
        wide[metric] = sub
    return wide


def _wilcoxon_pair(a: np.ndarray, b: np.ndarray) -> tuple[float, str]:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    d = a - b
    if np.all(d == 0):
        return 1.0, "all_diff_zero"
    try:
        res = wilcoxon(a, b, alternative="two-sided", zero_method="wilcox")
        return float(res.pvalue), "ok"
    except ValueError as e:
        return float("nan"), str(e)


def stars(p: float) -> str:
    if p != p:
        return ""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return ""


def holm_bonferroni(pvals: list[float]) -> list[float]:
    m = len(pvals)
    pv = np.array(
        [1.0 if (x != x or x is None) else float(x) for x in pvals],
        dtype=float,
    )
    order = np.argsort(pv)
    sorted_p = pv[order]
    adj_sorted = np.zeros(m, dtype=float)
    running = 0.0
    for i in range(m):
        running = max(running, min(1.0, (m - i) * sorted_p[i]))
        adj_sorted[i] = running
    out = np.empty(m, dtype=float)
    out[order] = adj_sorted
    return list(out)


def per_prompt_scores(
    df: pd.DataFrame,
    setting: str,
    metric: str,
    prompt_ids: list[int],
) -> np.ndarray:
    sub = df[df["_cond"] == setting]
    g = sub.groupby("prompt_id", sort=True)[metric].mean().reindex(prompt_ids)
    if g.isna().any():
        missing = g[g.isna()].index.tolist()
        raise ValueError(f"{setting}/{metric}: missing prompts {missing[:5]} ...")
    return g.to_numpy(dtype=float)


def bootstrap_mean_ci(
    x: np.ndarray,
    *,
    rng: np.random.Generator,
    n_boot: int,
    pct: tuple[float, float] = (2.5, 97.5),
) -> tuple[float, float, float]:
    x = np.asarray(x, dtype=float)
    n = x.shape[0]
    obs = float(np.mean(x))
    out = np.empty(n_boot, dtype=float)
    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        out[b] = float(np.mean(x[idx]))
    lo, hi = [float(v) for v in np.percentile(out, list(pct))]
    return obs, lo, hi


def pct_vs_null(v: float, null_v: float) -> str:
    if null_v == 0:
        return "n/a"
    p = (v - null_v) / null_v * 100.0
    sign = "+" if p > 0 else ""
    return f"{sign}{p:.1f}%"


def fmt_cell(mean: float, lo: float, hi: float, star: str) -> str:
    lo_r, hi_r = round(lo, 1), round(hi, 1)
    core = f"{mean:.3f} [{lo_r:g}, {hi_r:g}]"
    return core + star


def backend_prompt_series(
    df: pd.DataFrame,
    setting: str,
    backend: str,
    metric: str,
    prompts: list[int],
) -> np.ndarray:
    sub = df[(df["_cond"] == setting) & (df["backend"] == backend)]
    g = sub.groupby("prompt_id", sort=True)[metric].mean().reindex(prompts)
    if g.isna().any():
        raise ValueError(
            f"Missing {setting}/{backend}/{metric}: {g[g.isna()].index.tolist()[:5]}"
        )
    return g.to_numpy(dtype=float)


def mean_of_six_backend_means_bootstrap(
    aligned_series: list[np.ndarray],
    *,
    rng: np.random.Generator,
    n_boot: int,
    pct: tuple[float, float] = (2.5, 97.5),
) -> tuple[float, float, float]:
    if len(aligned_series) != 6:
        raise ValueError("Need 6 prompt-aligned series")
    n = len(aligned_series[0])
    if any(len(x) != n for x in aligned_series):
        raise ValueError("All six series must have the same length")
    obs = float(np.mean([float(x.mean()) for x in aligned_series]))
    out = np.empty(n_boot, dtype=float)
    for k in range(n_boot):
        idx = rng.integers(0, n, size=n)
        out[k] = float(np.mean([float(x[idx].mean()) for x in aligned_series]))
    lo, hi = [float(v) for v in np.percentile(out, list(pct))]
    return obs, lo, hi


def fmt_cell_with_pct(mean: float, lo: float, hi: float, star: str, null_ref: float) -> str:
    return f"{fmt_cell(mean, lo, hi, star)} ({pct_vs_null(mean, null_ref)})"


def collect_all_wilcoxon_tests(
    df: pd.DataFrame,
    prompts: list[int],
    null_by_metric: dict[str, np.ndarray],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    wide = prompt_level_means(df)
    pid = wide["prompt_id"]

    for setting in ("ablation", "full"):
        for backend in BACKEND_ORDER:
            for metric in METRIC_KEYS:
                x = backend_prompt_series(df, setting, backend, metric, prompts)
                y = null_by_metric[metric]
                p, note = _wilcoxon_pair(x, y)
                lab = f"{backend}_{'abl' if setting == 'ablation' else 'full'}_vs_null"
                rows.append(
                    {
                        "metric": metric,
                        "comparison": lab,
                        "block": "per_backend",
                        "setting": setting,
                        "backend": backend,
                        "n_prompts": len(prompts),
                        "p_two_sided": p,
                        "stars_uncorrected": stars(p),
                        "wilcoxon_note": note,
                    }
                )

    for metric in METRIC_KEYS:
        sub = wide[metric]
        for a, b, tag in (
            ("ablation", "null", "mean_ablation_vs_null"),
            ("full", "null", "mean_full_vs_null"),
            ("full", "ablation", "mean_full_vs_ablation"),
        ):
            x = sub[a].reindex(pid).to_numpy(dtype=float)
            y = sub[b].reindex(pid).to_numpy(dtype=float)
            p, note = _wilcoxon_pair(x, y)
            rows.append(
                {
                    "metric": metric,
                    "comparison": tag,
                    "block": "mean_aggregate",
                    "setting": "",
                    "backend": "",
                    "n_prompts": len(pid),
                    "p_two_sided": p,
                    "stars_uncorrected": stars(p),
                    "wilcoxon_note": note,
                }
            )

    raw_p = [float(r["p_two_sided"]) if r["p_two_sided"] == r["p_two_sided"] else 1.0 for r in rows]
    holm = holm_bonferroni(raw_p)
    for r, h in zip(rows, holm):
        r["p_holm"] = h
        r["stars_holm"] = stars(float(h))

    return rows


def _prefer_c_locale() -> None:
    """Use C locale when possible so numeric formatting and library messages stay English/ASCII."""
    for name in ("C", "C.UTF-8", "en_US.UTF-8"):
        try:
            locale.setlocale(locale.LC_ALL, name)
            return
        except locale.Error:
            continue


def main() -> None:
    _prefer_c_locale()

    ap = argparse.ArgumentParser(
        description="Full Table 2: per-cell 95% bootstrap CI and Wilcoxon stars vs null."
    )
    ap.add_argument(
        "--xlsx",
        type=Path,
        default=DEFAULT_XLSX,
        help=f"Path to workbook (default: <repo root>/{DEFAULT_TABLE2_WORKBOOK})",
    )
    ap.add_argument(
        "--sheet",
        default=DEFAULT_TABLE2_SHEET,
        help="Worksheet with the long table (default: %(default)s)",
    )
    ap.add_argument(
        "--n-boot",
        type=int,
        default=50_000,
        help="Bootstrap resamples for percentile CIs (default: %(default)s)",
    )
    ap.add_argument(
        "--seed",
        type=int,
        default=42,
        help="RNG seed for reproducible bootstrap (default: %(default)s)",
    )
    args = ap.parse_args()

    if not args.xlsx.is_file():
        raise FileNotFoundError(f"Excel file not found: {args.xlsx}")

    df = load_table2_dataset(args.xlsx, sheet=args.sheet)
    rng = np.random.default_rng(args.seed)
    prompts = sorted(df["prompt_id"].unique().tolist())

    for b in BACKEND_ORDER:
        for s in ("ablation", "full"):
            n = len(df[(df["_cond"] == s) & (df["backend"] == b)])
            if n != len(prompts):
                raise ValueError(f"backend {b} {s}: expected {len(prompts)} rows, got {n}")

    null_by_metric = {mk: per_prompt_scores(df, "null", mk, prompts) for mk in METRIC_KEYS}
    null_means = {mk: float(np.mean(null_by_metric[mk])) for mk in METRIC_KEYS}
    null_ci = {
        mk: bootstrap_mean_ci(null_by_metric[mk], rng=rng, n_boot=args.n_boot)
        for mk in METRIC_KEYS
    }

    wilcox_rows = collect_all_wilcoxon_tests(df, prompts, null_by_metric)

    def star_backend(setting: str, backend: str, metric: str) -> str:
        suff = "abl" if setting == "ablation" else "full"
        lab = f"{backend}_{suff}_vs_null"
        for r in wilcox_rows:
            if r["comparison"] == lab and r["metric"] == metric:
                return str(r["stars_uncorrected"] or "")
        return ""

    def star_mean(block: str, metric: str) -> str:
        tag = {"ablation": "mean_ablation_vs_null", "full": "mean_full_vs_null"}[block]
        for r in wilcox_rows:
            if r["comparison"] == tag and r["metric"] == metric:
                return str(r["stars_uncorrected"] or "")
        return ""

    series_ab: dict[str, list[np.ndarray]] = {
        mk: [backend_prompt_series(df, "ablation", b, mk, prompts) for b in BACKEND_ORDER]
        for mk in METRIC_KEYS
    }
    series_fu: dict[str, list[np.ndarray]] = {
        mk: [backend_prompt_series(df, "full", b, mk, prompts) for b in BACKEND_ORDER]
        for mk in METRIC_KEYS
    }

    ab_agg = {
        mk: mean_of_six_backend_means_bootstrap(
            series_ab[mk], rng=rng, n_boot=args.n_boot
        )
        for mk in METRIC_KEYS
    }
    fu_agg = {
        mk: mean_of_six_backend_means_bootstrap(
            series_fu[mk], rng=rng, n_boot=args.n_boot
        )
        for mk in METRIC_KEYS
    }

    header = ["Condition", "Executability", "Intent Align", "Script Quality"]
    rows_out: list[list[str]] = [header]

    null_row = ["null (baseline)"]
    for mk in METRIC_KEYS:
        m, lo, hi = null_ci[mk]
        null_row.append(fmt_cell(m, lo, hi, ""))
    rows_out.append(null_row)

    rows_out.append(["**Ablation setting**", "", "", ""])
    for bi, b in enumerate(BACKEND_ORDER):
        r = [f"{b}_abl."]
        for mk in METRIC_KEYS:
            x = series_ab[mk][bi]
            m, lo, hi = bootstrap_mean_ci(x, rng=rng, n_boot=args.n_boot)
            st = star_backend("ablation", b, mk)
            r.append(fmt_cell_with_pct(m, lo, hi, st, null_means[mk]))
        rows_out.append(r)

    mean_ab = ["**Mean**"]
    for mk in METRIC_KEYS:
        m, lo, hi = ab_agg[mk]
        st = star_mean("ablation", mk)
        mean_ab.append(fmt_cell_with_pct(m, lo, hi, st, null_means[mk]))
    rows_out.append(mean_ab)

    rows_out.append(["**Full setting**", "", "", ""])
    for bi, b in enumerate(BACKEND_ORDER):
        r = [f"{b}_full"]
        for mk in METRIC_KEYS:
            x = series_fu[mk][bi]
            m, lo, hi = bootstrap_mean_ci(x, rng=rng, n_boot=args.n_boot)
            st = star_backend("full", b, mk)
            r.append(fmt_cell_with_pct(m, lo, hi, st, null_means[mk]))
        rows_out.append(r)

    mean_fu = ["**Mean**"]
    for mk in METRIC_KEYS:
        m, lo, hi = fu_agg[mk]
        st = star_mean("full", mk)
        mean_fu.append(fmt_cell_with_pct(m, lo, hi, st, null_means[mk]))
    rows_out.append(mean_fu)

    xlsx_name = args.xlsx.name
    n_prompts = len(prompts)
    md_lines = [
        "## Table 2: Experimental Results (full grid, 95% CI per cell)",
        "",
        "**Why do some cells show stars?** Stars mark two-sided **paired** Wilcoxon signed-rank tests of that "
        f"cell's score series against the **null** baseline (_n_={n_prompts} prompts; scores are already averaged across "
        "the two raters). LLM rows use **single-backend** scores; Mean rows use **six-backend-averaged** prompt-level "
        "scores. * / ** / *** correspond to uncorrected *p* below 0.05 / 0.01 / 0.001; non-significant cells have **no** star. "
        "**Multiple comparisons:** **45** tests are defined (36 per-backend vs null + 9 mean-aggregate). "
        "Those nine include **mean full vs mean ablation** (three metrics), which are **not** marked with stars in the grid. "
        "Uncorrected and **Holm** *p* for all 45 are in `summary/wilcoxon_table2_all_cells.csv` (Holm adjusts over the full family). "
        "The grid uses uncorrected stars; Holm can be reported in the footnote, supplementary table, or both.",
        "",
        f"**Confidence intervals:** per-LLM cells bootstrap over that model's {n_prompts} prompt scores; **Mean** is the "
        f"arithmetic mean of six per-backend means, with CIs from **paired** bootstrap (same resampled indices for "
        f"all six series each draw; B={args.n_boot}, seed={args.seed}). Percent change vs null uses the **sample** grand mean of the null row. "
        f"**Data source:** workbook `{xlsx_name}`, sheet `{args.sheet}` only.",
        "",
    ]
    md_lines.append("| " + " | ".join(header) + " |")
    md_lines.append("| " + " | ".join(["---"] * 4) + " |")
    for r in rows_out[1:]:
        md_lines.append("| " + " | ".join(r) + " |")

    out_md = ROOT / "summary" / "table2_paper_full_grid.md"
    out_md.write_text("\n".join(md_lines), encoding="utf-8")

    out_csv = ROOT / "summary" / "table2_paper_full_grid.csv"
    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerows(rows_out)

    wcsv = ROOT / "summary" / "wilcoxon_table2_all_cells.csv"
    pd.DataFrame(wilcox_rows).to_csv(wcsv, index=False, encoding="utf-8-sig")

    pd.DataFrame(wilcox_rows).to_csv(
        ROOT / "summary" / "wilcoxon_recomputed_from_long_only.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print(f"Wrote {out_md}")
    print(f"Wrote {out_csv}")
    print(f"Wrote {wcsv} (45 tests, Holm in CSV)")


if __name__ == "__main__":
    main()
