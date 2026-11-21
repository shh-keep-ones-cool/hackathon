# Prompts used

Only the Stage 6 prompt was available to the assistant that wrote this file. **Stages 1–5 prompts must be pasted in by the team from their chat history**; they are not reconstructed here to avoid inventing them.

## Stage 1
1. From pci_concordance.csv build 4-5 bridge groups (mean of z-scored mapped
   indicators). Indicators with no old counterpart are used only in 2025.
2. Z-score within each year. Never put 2025 into the old-framework
   regressions and never compute "change 2024 to 2025".
3. Merge 63 to 34: sum counts, population and GRDP first, then compute rates
   and ln GRDP per capita. Merge PCI groups with survey-firm weights (else
   active-firm weights); also run unweighted and report if conclusions change.
QUALITY CHECKS
Print: merged totals equal pre-merger totals; every checks.md value; table of
provinces unchanged / renamed / merged / split. Say that merging reduces
within-province variation. Wait for me.

## Stage 2
In analysis/, for each outcome (firms_new_per1000, net_entry_rate, fdi_pc) and
each specification (with/without ln grdp_pc + coastal; with/without HCMC and
Hanoi) compute: correlation matrix and VIF of the 9 sub-indices; standardised
OLS per sub-index with HC3; Ridge with leave-one-out alpha and 1,000 bootstrap
intervals; Spearman; the share of specifications where each sub-index stays in
the top three; and the difference between each province's score and the score
predicted by ln GRDP per capita. Save to data/model_results.csv. Comment every
step. Then write the same per-sub-index OLS in JavaScript and print the
largest difference to Python.
QUALITY CHECKS
Largest difference below 0.000001. Report leave-one-out R2 and say plainly if
near zero or negative. Report VIF above 5 and name the sub-indices that cannot
be separated. List every exclusion. No causal language. Wait for me.

## Stage 3
1. Build ln(new firms per 1000) for t+1, t+2, t+3.
2. For each bridge group (z-scored within year) estimate outcome(t+k) on
   group(t) with province and year fixed effects, errors clustered by province.
3. Compare sign and rank with Stage 2. A group is "stable" only if the sign
   agrees in both AND the interval excludes 0. Labels: stable = "strong
   priority candidate"; otherwise "low reliability".
4. State provinces and years entered; list every exclusion.
5. State that PCI is a perception survey, that fixed effects remove only
   time-invariant confounders, and that the 2025 break limits comparison.
QUALITY CHECKS
Print the table before any chart. Wait for me.

## Stage 4
Build the one-screen page for one province. Headline template, filled from
data: "To attract firms, [province] should invest first in [group]: it is [x]
below similar provinces, and the link holds in both 2025 and the panel
(n=[..])." Three key numbers (Level, Benchmark, Trend). Main chart: dot plot
of gap to peer median by bridge group, province highlighted, income-predicted
score marked. Detail: priority table (gap, 2025 coefficient, panel
coefficient, stability label, horizon, cost) with the scoring formula shown.
Map coloured by selected group. Footer: sources, date, method.
QUALITY CHECKS
Every number traceable to a CSV. Compare with checks.md. Test with 3
provinces including HCMC. Avoid red-green only; check a phone-width layout.
Wait for me.

## Stage 5
Add controls: province; peer set (similar income / region / all); exclude
HCMC and Hanoi; evidence (2025 only / panel only / both). Peer averages
always exclude the selected province. Add a scenario slider: "if [group] rose
to the peer median, the outcome would differ by [low, high]" using bootstrap
intervals, worded as association, not a forecast.
QUALITY CHECKS
Switching HCMC/Hanoi reproduces the Stage 2 specification values. State the
n of the current selection. Wait for me.

## Stage 6
Act as a sceptical judge. Recompute the 3 numbers you would question first and show the steps. List the 5 hardest questions on method, data and policy relevance and whether the page answers each. Check wording for causality. Prepare: README (question, sources, data roles, AI/LLM declaration), prompts used, docs/LIMITATIONS.md, and an English presentation outline with a short Vietnamese summary, led by the recommendation. QUALITY CHECKS: No private data in the repo. Every limitation visible on the page.
