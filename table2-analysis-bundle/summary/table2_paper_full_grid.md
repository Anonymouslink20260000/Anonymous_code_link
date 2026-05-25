## Table 2: Experimental Results (full grid, 95% CI per cell)

**Why do some cells show stars?** Stars mark two-sided **paired** Wilcoxon signed-rank tests of that cell's score series against the **null** baseline (_n_=120 prompts; scores are already averaged across the two raters). LLM rows use **single-backend** scores; Mean rows use **six-backend-averaged** prompt-level scores. * / ** / *** correspond to uncorrected *p* below 0.05 / 0.01 / 0.001; non-significant cells have **no** star. **Multiple comparisons:** **45** tests are defined (36 per-backend vs null + 9 mean-aggregate). Those nine include **mean full vs mean ablation** (three metrics), which are **not** marked with stars in the grid. Uncorrected and **Holm** *p* for all 45 are in `summary/wilcoxon_table2_all_cells.csv` (Holm adjusts over the full family). The grid uses uncorrected stars; Holm can be reported in the footnote, supplementary table, or both.

**Confidence intervals:** per-LLM cells bootstrap over that model's 120 prompt scores; **Mean** is the arithmetic mean of six per-backend means, with CIs from **paired** bootstrap (same resampled indices for all six series each draw; B=50000, seed=42). Percent change vs null uses the **sample** grand mean of the null row. **Data source:** workbook `table2_dataset.xlsx`, sheet `raw_data` only.

| Condition | Executability | Intent Align | Script Quality |
| --- | --- | --- | --- |
| null (baseline) | 95.000 [90.8, 98.3] | 56.000 [50.2, 61.8] | 58.000 [52.5, 63.5] |
| **Ablation setting** |  |  |  |
| qwen4b_abl. | 100.000 [100, 100]* (+5.3%) | 47.833 [45.8, 49.8]* (-14.6%) | 42.167 [39.8, 44.5]*** (-27.3%) |
| llama8b_abl. | 97.500 [94.2, 100] (+2.6%) | 67.583 [63.1, 72.2]*** (+20.7%) | 69.083 [64.8, 73.3]** (+19.1%) |
| deepseek16b_abl. | 74.583 [66.7, 82.1]*** (-21.5%) | 47.417 [43.8, 51]* (-15.3%) | 47.750 [44.1, 51.5]** (-17.7%) |
| claude_abl. | 97.500 [94.2, 100] (+2.6%) | 48.000 [45.5, 50.5]* (-14.3%) | 45.833 [42.8, 48.8]*** (-21.0%) |
| qwenmax_abl. | 87.500 [80.8, 93.3]* (-7.9%) | 65.667 [61.3, 69.8]** (+17.3%) | 60.917 [56.2, 65.6] (+5.0%) |
| gpt-4omini_abl. | 95.833 [91.7, 99.2] (+0.9%) | 56.167 [52.8, 59.5] (+0.3%) | 58.750 [56, 61.7] (+1.3%) |
| **Mean** | 92.153 [90.1, 94]*** (-3.0%) | 55.444 [53.9, 57] (-1.0%) | 54.083 [52.3, 55.9] (-6.8%) |
| **Full setting** |  |  |  |
| qwen4b_full | 100.000 [100, 100]* (+5.3%) | 69.833 [67.3, 72.3]*** (+24.7%) | 70.000 [67.3, 72.7]*** (+20.7%) |
| llama8b_full | 98.333 [95.8, 100] (+3.5%) | 72.083 [67.1, 76.8]*** (+28.7%) | 70.333 [65.5, 75]*** (+21.3%) |
| deepseek16b_full | 96.250 [92.5, 99.2] (+1.3%) | 72.500 [68.8, 75.8]*** (+29.5%) | 73.833 [70.2, 77.2]*** (+27.3%) |
| claude_full | 100.000 [100, 100]* (+5.3%) | 82.000 [79.8, 84.2]*** (+46.4%) | 78.833 [76, 81.7]*** (+35.9%) |
| qwenmax_full | 96.250 [92.5, 99.2] (+1.3%) | 75.250 [72.1, 78.4]*** (+34.4%) | 70.417 [66.7, 74.2]*** (+21.4%) |
| gpt-4omini_full | 97.917 [95, 100] (+3.1%) | 69.000 [65.5, 72.5]*** (+23.2%) | 68.833 [65.3, 72.3]** (+18.7%) |
| **Mean** | 98.125 [97.1, 99] (+3.3%) | 73.444 [71.9, 75]*** (+31.2%) | 72.042 [70.4, 73.7]*** (+24.2%) |