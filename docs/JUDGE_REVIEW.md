# Stage 6 sceptical review

Reviewer: Claude (AI), working only from the uploaded files. Recomputation code: `analysis/08_recompute_checks.py`. The node suite (`analysis/test_stage5.js`) passes 1316 checks before and after the edits below. I did not open the page in a browser; headlines and the limitations block were checked through `dashboard_core.js` and the built HTML text.

## A. Three numbers recomputed

**1. HCMC default headline: shortfall in "integrity and fair competition" = 1.0087 SD (page: 1.0).**
1. G4 = `pci_s5 + pci_s6` (`bridge_groups.csv`). z-score each across the 34 (ddof = 1), average, z-score again. HCMC = −0.6987; rank 25 of 34.
2. Peers: quartile of ln(GRDP/pop 2024); edges 4.2507 / 4.3837 / 4.6128; HCMC is in quartile 4 (GRDP per capita rank 2) with 8 peers: Bắc Ninh, Đồng Nai, Hà Nội, Hải Phòng, Khánh Hòa, Quảng Ninh, Tây Ninh, Thái Nguyên.
3. Peer median = 0.3100, gap = −0.6987 − 0.3100 = **−1.0087**. Matches the page.
4. Sensitivity: "all other provinces" gives −0.8448. Peer scores range from −0.76 to +1.45, so the median of 8 is itself noisy.
*My first attempt used the G5 columns by mistake and produced −0.0107, which equals the dashboard's G5 row; corrected above.*

**2. 2025 association, G1 (market entry): coef 0.1675, HC3 SE 0.0937.**
1. y = firms_new / pop (thousands) = new firms per 1000; x = `pci_s1`; OLS with intercept, n = 34. Coef 0.167506, HC3 SE 0.093723 (equals Stage 2 table).
2. 95% interval −0.016 to 0.351 with 1.96; with t(32) it is −0.023 to 0.358 (p 0.074 vs 0.083). Standardised coef 0.1589 = what the page shows.
3. Drop-one range 0.135–0.229; without HCMC and Hà Nội 0.157 (SE 0.091). Stable in size, never distinguishable from 0 in the default setting.
4. Timing: the 2025 file's firm counts equal the 2024 NSO values exactly, so the outcome precedes the 2025 survey.

**3. Panel, transparency and compliance (G3), 2 years later: coef 0.0359, +3.65% per SD, p = 0.0485.**
1. Two-way demeaning of ln(new firms per 1000) at t+2 on the within-year z-score, 34 provinces × 7 years (N = 238). Coef 0.035882 = file value; 100(e^b − 1) = 3.653.
2. Cluster SE: CR0 0.01704, CR1 0.01729, CR1 with (N−1)/(N−T) 0.01752 = file value (so the file uses that small-sample factor and t(33)). Interval 0.0002 to 0.0715.
3. The lower bound is 0.0002 above zero. The bootstrap interval is 0.0059 to 0.0749. This is the only result that makes any group a "strong priority candidate" in the panel.
4. Same procedure at 3 years (the default): G1 −0.0154 (file −0.0154), G5 +0.0372 (p 0.136). Signs for G1 go +, +, − across 1, 2, 3 years.

**Consequence found while checking.** With default switches, no province gets a priority label at 1 or 3 years; 16 of 34 do at 2 years. Of 180 (group × setting) combinations 17 are labelled strong. The default horizon therefore decides whether the page recommends anything.

## B. Five hardest questions

| # | Question | Does the page answer it? |
|---|---|---|
| 1 | **Method / causality.** Why read a 34-province association as guidance to invest? Fixed effects do not remove province-by-year shocks, and firms may influence ratings. | **Partly, before edits.** Banner and scenario said "association", but the headline said "To attract firms, X should invest first". Fixed: headline now says "a candidate to review, not evidence that investing…"; L1 lists the timing problem. |
| 2 | **Method / measurement.** Panel slopes come from the legacy PCI, shortfalls from PCI 2.0. Why can they be combined? | **No, before edits.** The break was mentioned, but the scenario multiplied them without a warning. Now stated in the scenario note and L2. The bridge is by name; components are not reconciled (`pci_concordance.csv`). Still unresolved, only disclosed. |
| 3 | **Method / inference.** 15 panel tests plus switches, one result at p = 0.049, sign flips, ridge LOO R² ≈ −0.02. Is anything real? | **Partly.** Labels show "low reliability" and the footer gave the R². Multiple comparisons and the 2-year/3-year contrast were not shown. Now in L5 and L6. No correction for multiplicity was applied. |
| 4 | **Data / ranking.** Priority = shortfall ÷ an assumed cost. How much does the order depend on invented costs? | **Partly.** Costs were labelled assumptions, but no sensitivity. Equal costs change the top group for 7 of 32 provinces (now L7). Costs should be elicited from officials or removed. |
| 5 | **Policy relevance.** What can a province do with "close the gap to the peer median", and is new-firm count the right goal? | **Weakly.** The outcome was not defined on the page and nothing said a province cannot set perceptions. Now L8, L9, L10. The tool supports diagnosis and further inquiry, not a spending decision. |

## C. Wording check for causality

Changed:
- Headline "To attract firms, … should invest first in …" → neutral, "candidate to review". "Attract" implied inward investment, which is not what the outcome measures.
- "3 years (assumed reform lag)" → "3 years (default; an assumption)". "Reform lag" asserted a mechanism.
- Scenario note: added that the panel slope is legacy-framework.

Left, with reasons: "association" and "provinces scoring that much higher had…" (descriptive); "strong priority candidate" (a label about evidence consistency plus shortfall, defined on the page; consider renaming "consistent signal" to avoid reading it as a verdict); "Scenario: closing the gap" (the section subtitle says "An association in past data, not a forecast").

## D. Quality checks

- **Private data:** regex scan for e-mails, phones, keys, local paths found none; data are public province aggregates. `pci_panel_63_bak_20261121_095021.csv` (all PCI cells empty) and `outcomes_panel_63_before_gso_import.csv` are stale backups; they are listed in `.gitignore` and should not be committed. The page loaded Google Fonts on every visit, which sent each viewer's address to a third party and contradicted "computed in your browser"; removed (system font stack).
- **Limitations on the page:** 12 of 12 present (`analysis/07_check_limitations.py`).
- **Files to reconcile:** the uploaded `model_results.csv` is the old Stage 2 table (9 rows); the one embedded in the page has 3,425 rows with a different schema. The test expects Stage 2 values hard-coded. Keep them under different names.
- **Not done:** no browser rendering test, no screen-reader check, mobile layout not inspected.
