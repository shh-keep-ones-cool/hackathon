# Known values (checks only; never use these as model inputs)

| ID | Check | Expected | Source |
|---|---|---|---|
| C1 | Number of provinces in `pci_provinces.csv` for PCI 2025 | 34 | VCCI, https://pcivietnam.vn/report-2025 |
| C2 | `pci_s1` (Gia nhập thị trường) of Bắc Ninh, 2025 | 8.20 | VCCI PCI 2025 page, 34-province component table: https://pcivietnam.vn/report-2025 |
| C3 | `pci_s4` (Chi phí tuân thủ TTHC) of Cà Mau, 2025 | 8.06 | VCCI PCI 2025 page, 34-province component table: https://pcivietnam.vn/report-2025 |
| C4 | BPI total of Quảng Ninh, 2025 | 5.33 | VCCI PCI 2025 page, BPI table: https://pcivietnam.vn/report-2025 |
| C5 | After 63→34 aggregation, total `firms_new`, `firms_active`, and `pop` by year vs pre-aggregation totals | equal within 1e-6 where values are complete | Crosswalk based on Resolution 202/2025/QH15: https://baochinhphu.vn/nghi-quyet-cua-quoc-hoi-ve-sap-xep-don-vi-hanh-chinh-cap-tinh-102250612191145158.htm |
| C6 | Share sum for every `old_province_id` | 1.000000 | `data/crosswalk_63_to_34.csv`; source: Resolution 202/2025/QH15 |
| C7 | Maximum absolute difference in simple OLS coefficients, JavaScript vs Python, same complete cases | < 0.000001 | `analysis/ols_reference.js` vs `analysis/test_ols_parity.py` |
| C8 | Number of PCI 2025 survey participants reported by VCCI | 5,128 businesses and business households (national total; do not write this as province-level n) | VCCI / PCI 2.0 release information: https://en.vcci.com.vn/vcci-news/pci-20-when-reform-is-measured-by-business-growth-120587 |

**Important check interpretation:** VCCI's PCI 2025 page publishes the component scores and quality groups; it does not provide a comparable PCI 2025 total-score rank list. Therefore there is deliberately no “rank of province A by `pci_total`” check. Do not invent such a rank. Similarly, the GSO national sum for 2025 newly registered enterprises must be entered only after exporting the same definition/reference period from the relevant NSO table; until then, that reconciliation is `PENDING`, not a passed check.
