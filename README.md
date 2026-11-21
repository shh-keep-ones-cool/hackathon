# PCI 2.0 Dashboard: Provincial Governance, Peer Gaps and New Firm Formation

## 1. Project overview

This project examines how provinces and centrally governed cities compare on the nine PCI 2.0 sub-indices published for 2025, and whether related governance dimensions are associated with new enterprise formation in historical data.

The dashboard is designed as a decision-support and exploratory benchmarking tool. It helps users:

- Compare a province with a selected peer group.
- Identify governance dimensions where its score is below the peer median.
- Examine associations between governance indicators and newly registered enterprises per 1,000 residents.
- Explore how results change under alternative peer sets, horizons and evidence rules.

**The analysis does not establish causality and should not be used as a stand-alone basis for allocating public reform budgets.**

See [Limitations](docs/LIMITATIONS.md) and [Presentation](docs/PRESENTATION.md).

## 2. Research question

# Which PCI sub-index should a province prioritize improving in order to support private sector development?

The outcome is newly registered enterprises per 1,000 residents. It is not a direct measure of inward investment, job creation, firm survival or productivity.

## 3. Main recommendation

Use the dashboard to benchmark provincial governance and identify questions for further investigation.

Do not interpret a priority label as proof that improving a particular sub-index will increase enterprise formation. The panel uses the legacy PCI framework, while the provincial comparison uses PCI 2.0 (2025). The two frameworks are not directly equivalent.

The current presentation identifies a borderline association for transparency and compliance at a two-year horizon. This result is sensitive to the selected horizon and multiple comparisons. At the default three-year horizon, no province receives a priority label under the default evidence rule.

See `docs/PRESENTATION.md` for the presentation narrative and `docs/LIMITATIONS.md` for the complete limitations.

## 4. Repository structure

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
│   ├── gso_pxweb_query_template.json
│   ├── pci_historical_column_map_template.xlsx
│   ├── pci_historical_mapping_verified.csv
│   └── pci_manual_entry_2010_2024.csv
├── data/
│   ├── raw/
│   │   └── gso/
│   ├── crosswalk_63_to_34.csv
│   ├── derived_features_2025.csv
│   ├── model_results.csv
│   ├── outcomes_panel_34.csv
│   ├── outcomes_panel_63.csv
│   ├── pci_bpi_2025.csv
│   ├── pci_concordance.csv
│   ├── pci_panel_63.csv
│   ├── pci_provinces.csv
│   └── pci_subindex_meta.csv
├── docs/
│   ├── AI_USE.md
│   ├── JUDGE_REVIEW.md
│   ├── LIMITATIONS.md
│   ├── PRESENTATION.md
│   ├── PROMPTS.md
│   ├── index.html
│   └── source_log_template.csv
├── tests/
├── CLAUDE.md
├── SETUP_VI.md
├── checks.md
├── index.html
└── requirements.txt
