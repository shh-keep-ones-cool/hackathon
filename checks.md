# Data and Analysis Checks

This file defines verification targets only.

**A check must not be marked PASS until the corresponding test has actually been executed and its output reviewed.**

## 1. Data checks

| ID | Check | Expected result | Verification source | Status |
|---|---|---|---|---|
| C1 | Number of provinces in PCI 2025 dataset | 34 unique provinces | `data/pci_provinces.csv` | PENDING |
| C2 | Province IDs in PCI dataset | No duplicate IDs | `data/pci_provinces.csv` | PENDING |
| C3 | Number of PCI 2.0 sub-indices | 9 | VCCI PCI 2.0 source and `data/pci_provinces.csv` | PENDING |
| C4 | BPI treatment | Stored separately from PCI sub-indices | `data/pci_bpi_2025.csv` | PENDING |
| C5 | Crosswalk share by old province | Sum equals 1 | `data/crosswalk_63_to_34.csv` | PENDING |
| C6 | Crosswalk coverage | All 63 old provinces are mapped | `data/crosswalk_63_to_34.csv` | PENDING |

## 2. Geographic aggregation checks

| ID | Check | Expected result | Verification source | Status |
|---|---|---|---|---|
| C7 | Aggregated enterprise counts | Totals conserved where source data are complete | `analysis/aggregate_old_to_new.py` | PENDING |
| C8 | Aggregated population | Totals conserved where source data are complete | `analysis/aggregate_old_to_new.py` | PENDING |
| C9 | GRDP per capita aggregation | Population-weighted mean; never summed | `analysis/aggregate_old_to_new.py` | PENDING |
| C10 | Province-year key | No duplicate province-year records | Outcomes panel files | PENDING |

## 3. Statistical checks

| ID | Check | Expected result | Verification source | Status |
|---|---|---|---|---|
| C11 | Python model sample | Complete cases only; actual n reported | `analysis/derive_and_model.py` | PENDING |
| C12 | OLS parity | Python and JavaScript estimates agree within the documented tolerance | `analysis/test_ols_parity.py` and `analysis/test_stage5.js` | PENDING |
| C13 | Bootstrap reproduction | Point estimates reproduce the specified reference estimates | `analysis/06a_bootstrap.py` | PENDING |
| C14 | Causal interpretation | Results described as associations, not causal effects | Model outputs and presentation | PENDING |

## 4. Dashboard checks

| ID | Check | Expected result | Verification source | Status |
|---|---|---|---|---|
| C15 | Limitation disclosure | All 12 limitations are present | `analysis/07_check_limitations.py` and `docs/LIMITATIONS.md` | PENDING |
| C16 | Dashboard values | Displayed values trace back to data or documented calculations | Dashboard and source CSV files | PENDING |
| C17 | Missing values | Displayed as missing, not silently converted to zero | Dashboard | PENDING |
| C18 | Peer benchmark | Selected province excluded from its own peer benchmark | Dashboard logic | PENDING |

## 5. External source references

- VCCI PCI 2.0: https://pcivietnam.vn/report-2025
- Resolution 202/2025/QH15 on provincial administrative reorganization: https://baochinhphu.vn/nghi-quyet-cua-quoc-hoi-ve-sap-xep-don-vi-hanh-chinh-cap-tinh-102250612191145158.htm
- VCCI PCI 2.0 announcement: https://en.vcci.com.vn/vcci-news/pci-20-when-reform-is-measured-by-business-growth-120587

Verify the original source and the exact definition before using any value as a confirmed benchmark.

## 6. Status definitions

- `PENDING`: Not yet executed or independently verified.
- `PASS`: Executed and meets the expected result.
- `FAIL`: Executed and does not meet the expected result.
- `N/A`: Not applicable, with an explanation.

Do not change a status to PASS based only on an expected value or a previous AI-generated statement.