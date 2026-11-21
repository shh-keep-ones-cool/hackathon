# PCI 2.0 dashboard: where do provinces fall short, and does it matter for new firms?

## Question
Which PCI sub-indices should provinces and cities invest in to attract businesses? The answer is an **association in public data, not evidence of cause**; see `docs/LIMITATIONS.md` (all 12 items are also in the page footer).

## Recommendation in one line
Use the dashboard to benchmark and to choose what to investigate. Do not allocate reform budgets from it yet: at the default 3-year horizon no province gets a priority label, and the one signal that appears (transparency and compliance, 2-year horizon) is borderline. Details: `docs/PRESENTATION.md`.

## Open
`dashboard.html` is one self-contained file (no network requests). Open it in a browser; `#ha-noi` style links select a province.

## Sources (public aggregates, no personal or firm-level data)
- PCI 2.0 (2025) sub-indices and business-performance index: VCCI PCI 2025 report page, accessed 2026-11-20.
- Legacy PCI 2010\u20132024 for 63 provinces: `pci_panel_63.csv` (source note per file to be completed by the data owner).
- New firms, active firms, population, GRDP 2018\u20132024: NSO Excel workbooks V05.02, V05.04, V02.03-07, V03.12, V03.10, accessed 2026-11-21 (cited by workbook code; add URLs).
- Merger 63 \u2192 34: Resolution 202/2025/QH15 (`crosswalk_63_to_34.csv`). Boundaries: `vn_provinces.geojson`, simplified for display.

## Data roles
| Role | Files |
|---|---|
| Raw input (as obtained) | `pci_provinces`, `pci_bpi_2025`, `pci_panel_63`, `outcomes_panel_63`, `crosswalk_63_to_34`, `pci_concordance`, `pci_subindex_meta`, `vn_provinces.geojson` |
| Derived by scripts | `outcomes_34_rebuilt`, `bridge_groups`, `pci_groups_34_panel`, `derived_features_2025`, `model_results`, `bootstrap_results` |
| Embedded in the page | `pci_provinces`, `outcomes_34_rebuilt`, `bridge_groups`, `pci_subindex_meta`, `pci_groups_34_panel`, `model_results`, `pci_bpi_2025`, `bootstrap_results` (hashes in the footer) |
| Team assumptions, not measurements | horizon and cost levels in `pci_subindex_meta.csv` |
| Do not commit | `*_bak_*.csv`, `outcomes_panel_63_before_gso_import.csv` (see `.gitignore`) |
| Empty placeholders | `fdi_pc`, `public_invest_pc`, `budget_revenue_pc`, `pm25_mean`, `pci_total`, `grdp` columns of `pci_provinces.csv` |

Note: `model_results.csv` exists in two schemas (old 9-row Stage 2 table; current 3,425-row table). Keep the old one as `model_results_stage2.csv`.

## Rebuild and test
```
python analysis/06a_bootstrap.py        # writes data/bootstrap_results.csv (stops if Stage 2 numbers differ)
python analysis/06_build_dashboard.py   # writes dashboard.html
node analysis/test_stage5.js            # 1316 checks
python analysis/07_check_limitations.py # every limitation is on the page
python analysis/08_recompute_checks.py  # independent recomputation used in docs/JUDGE_REVIEW.md
```
Requires Python 3 with numpy, pandas, scipy, and Node 18+.

## AI / LLM declaration
Claude (Anthropic) was used to write and review the analysis scripts, the dashboard code, tests and these documents, in conversation with the team. The Stage 6 review recomputed three numbers independently and found one wording problem and two undisclosed issues (see `docs/JUDGE_REVIEW.md`). The team is responsible for the data collection, the choice of horizons and costs, and every claim. AI output was checked by running the scripts and tests, not by trusting the text. Prompts: `docs/PROMPTS.md`.
