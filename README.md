# PCI 2.0 Dashboard: Provincial Governance and New Firm Formation

## 1. Project overview

This project explores how provinces and centrally governed cities compare across the nine PCI 2.0 sub-indices published for 2025, and examines whether governance indicators are associated with new enterprise formation.

The dashboard is an exploratory benchmarking and decision-support tool. It helps users:

- Compare a selected province with a relevant peer group.
- Identify PCI 2.0 dimensions where a province scores below its peers.
- Explore statistical associations between governance indicators and new enterprise formation.
- Examine how findings change under different peer groups and analytical assumptions.

**The analysis does not establish causality and should not be used as a stand-alone basis for allocating public reform budgets.**

## 2. Research question

**Which PCI sub-index should provinces and cities prioritize investigating to support private-sector development?**

The main outcome is newly registered enterprises per 1,000 residents. It does not directly measure inward investment, job creation, firm survival or productivity.

## 3. Interpretation and recommendation

Use the dashboard to benchmark governance indicators and identify areas for further investigation.

Do not interpret a priority label as proof that improving a particular sub-index will increase enterprise formation.

The project uses two distinct PCI frameworks:

- PCI 2.0 (2025): the current framework with nine sub-indices.
- Legacy PCI (2010–2024): the historical framework used for panel analysis.

These frameworks are not directly equivalent. Historical associations must not be presented as direct estimates of the effect of PCI 2.0 scores.

See:
- [Limitations](docs/LIMITATIONS.md)
- [Presentation outline](docs/PRESENTATION.md)
- [AI use disclosure](docs/AI_USE.md)

## 4. Data sources and roles

| File | Role |
|---|---|
| `data/pci_provinces.csv` | 2025 PCI sub-indices and province-level inputs |
| `data/pci_bpi_2025.csv` | Separate 2025 BPI data |
| `data/pci_panel_63.csv` | Historical PCI data under legacy frameworks |
| `data/outcomes_panel_63.csv` | Historical outcomes for the 63 former provinces |
| `data/outcomes_panel_34.csv` | Outcomes aggregated to the 34-province geography |
| `data/crosswalk_63_to_34.csv` | Geographic crosswalk from 63 to 34 provinces |
| `data/pci_concordance.csv` | Conceptual mapping between PCI indicators |
| `data/pci_subindex_meta.csv` | Display metadata and team-defined assumptions |
| `data/derived_features_2025.csv` | Derived analytical variables |
| `data/model_results.csv` | Statistical model outputs |

Original source files and intermediate data are stored under `data/raw/` where applicable.

## 5. Methodological rules

### PCI 2.0 and historical PCI

- PCI 2.0 (2025) has nine sub-indices.
- BPI is a separate measure and must not be treated as a PCI sub-index or PCI total.
- Historical PCI scores use earlier frameworks and must retain their year-specific definitions.
- Do not calculate a direct 2024–2025 PCI change.

### Geographic harmonization

The 63-to-34 crosswalk is used to aggregate outcomes and population.

- Allocate counts and population using the crosswalk shares, then aggregate.
- Calculate per-capita measures after aggregation where appropriate.
- Aggregate GRDP per capita using population weights.
- Never sum or average old PCI scores to create a new-province PCI score.

### Outcome interpretation

Newly registered enterprises per 1,000 residents measure local firm formation.

They do not directly measure:
- Investment attracted.
- Number of jobs created.
- Firm survival.
- Business productivity.

### Statistical interpretation

- Regression estimates represent associations, not causal effects.
- Report the sample size, period, specification and uncertainty.
- Use complete cases for each model.
- Missing values must not be treated as zero.
- Distinguish observed results from assumptions assigned by the team.

## 6. Repository structure

```text
.
├── analysis/
│   ├── 06_build_dashboard.py
│   ├── 06a_bootstrap.py
│   ├── 07_check_limitations.py
│   ├── 08_recompute_checks.py
│   ├── aggregate_old_to_new.py
│   ├── build_geojson.py
│   ├── common.py
│   ├── dashboard_core.js
│   ├── dashboard_template.html
│   ├── derive_and_model.py
│   ├── fetch_gso_pxweb.py
│   ├── import_gso_34.py
│   ├── import_historical_pci.py
│   ├── scrape_pci_2025.py
│   ├── test_ols_parity.py
│   ├── test_stage5.js
│   └── validate_data.py
├── config/
├── data/
│   └── raw/
├── docs/
│   ├── AI_USE.md
│   ├── JUDGE_REVIEW.md
│   ├── LIMITATIONS.md
│   ├── PRESENTATION.md
│   ├── PROMPTS.md
│   └── source_log_template.csv
├── tests/
├── CLAUDE.md
├── checks.md
├── index.html
└── requirements.txt