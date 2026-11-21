# Limitations

These twelve items are the same list that appears in the footer of `dashboard.html` (ids `L1`–`L12`). `analysis/07_check_limitations.py` fails if any is missing from the page.

**L1. Association, not cause.** 34 provinces, observational data. Fixed effects remove only time-invariant province differences, not shocks that differ by province and year. Firms may also shape how they rate government (reverse direction): the 2025 scores are paired with 2024 firm counts, so the outcome comes before the score.

**L2. Framework break.** PCI 2.0 (2025) and the legacy PCI (2010–2024) differ in indicators and scale; groups are bridged by name and component indicators are not reconciled. Panel slopes are estimated on legacy scores but the scenario applies them to 2025 gaps, so the panel range is indicative only. No 2024-to-2025 change is computed.

**L3. Province merger.** 63 provinces became 34. Scores and outcomes before 2025 are merged with fixed 2018 active-firm weights; merged units are reconstructions and their institutions are still changing.

**L4. Small sample.** 34 provinces and 34 clusters; most intervals include 0. Percentile bootstrap intervals can be too narrow with few clusters, and the 2025 intervals use 1.96 where the panel uses t(33).

**L5. Many comparisons, fragile labels.** One borderline result (transparency and compliance, 2-year horizon, p ≈ 0.049) produces most priority labels. With the default peer set and evidence rule, no province gets a priority label at 1 or 3 years and 16 of 34 do at 2 years. Treat labels as exploratory.

**L6. Weak out-of-sample prediction.** The nine sub-indices do not predict new firms per 1000 out of sample (leave-one-out R² of the ridge model ≈ −0.02; a mean-only model scores −0.06).

**L7. Costs and horizons are assumptions.** The priority score divides the shortfall by a team-assigned cost level. Setting all costs equal changes the top group for 7 of the 32 provinces that have a ranked group.

**L8. Peer median is a convention.** The target and the peer set (for example 8 provinces for HCMC) are choices; with fewer than 5 peers the median is unstable. HCMC and Hà Nội are outliers; use the switch to see results without them.

**L9. Outcome.** New firms per 1000 residents (newly registered enterprises, NSO workbooks) measures local firm formation. It is not investment attracted, jobs, firm survival or productivity.

**L10. Perception data.** PCI is a survey of firms; who answers can change. Scores are relative (z-scores across the 34), so SD units say nothing about absolute quality, and a province cannot set perceptions directly.

**L11. Coverage.** Outcomes cover 2018–2024 only. Columns for FDI, public investment, budget revenue and PM2.5 are empty and unused; income control is ln GRDP per capita 2024.

**L12. Provenance.** Public aggregate statistics accessed 2026-11-20/21; NSO sources are cited by workbook code, not URL. Re-check before reuse. No personal or firm-level data are included.
