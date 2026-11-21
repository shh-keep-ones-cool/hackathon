# Stage 6 — Sceptical Review

## 1. Purpose

This review evaluates the project from the perspective of a critical research and case-competition judge.

The main objectives are to assess:

- Methodological validity.
- Data quality and traceability.
- Statistical interpretation.
- Dashboard usability.
- Policy relevance.
- Transparency of assumptions and limitations.

This document is a review record, not a substitute for independently reproducing every result.

## 2. Main methodological concerns

### 2.1 Association is not causation

The project uses observational provincial data.

Fixed effects can account for time-invariant differences between provinces and common year effects, but they cannot eliminate all time-varying confounding factors.

Reverse causality may also exist because businesses' perceptions of governance can be influenced by business conditions.

**Required presentation rule:** Use "associated with" rather than "causes", "drives" or "leads to".

### 2.2 PCI framework discontinuity

PCI 2.0 in 2025 differs from the historical PCI framework.

Historical panel estimates cannot automatically be interpreted as the effects of improving PCI 2.0 sub-indices.

The conceptual concordance between indicators does not establish numerical equivalence.

**Required presentation rule:** Clearly distinguish historical panel evidence from 2025 benchmarking.

### 2.3 Small sample and statistical uncertainty

The 2025 cross-section contains only 34 provinces.

Small samples can produce unstable coefficients and wide confidence intervals. Multiple comparisons can also increase the likelihood of borderline statistical findings.

**Required presentation rule:**

- Report sample size.
- Show confidence intervals where available.
- Avoid treating a borderline p-value as conclusive evidence.
- Disclose the number of comparisons and alternative specifications.

### 2.4 Assumed costs and time horizons

The project uses team-defined assumptions for reform costs and analytical horizons.

These are not observed government expenditure data or verified reform implementation timelines.

**Required presentation rule:** Label these values as "Team assumptions" wherever they appear.

### 2.5 Outcome measurement

Newly registered enterprises per 1,000 residents measure local firm formation.

They do not directly measure:

- Investment attracted.
- Employment created.
- Firm survival.
- Firm productivity.

**Required presentation rule:** Do not describe the outcome as a direct measure of investment attraction.

## 3. Data and reproducibility review

The following checks should be completed before final submission:

| Area | Required verification |
|---|---|
| PCI 2025 | Compare all province-level sub-index values with the original VCCI source |
| BPI | Confirm it remains separate from PCI sub-indices |
| Historical PCI | Verify year-specific source files and column mappings |
| NSO/GSO outcomes | Verify table codes, units, reference periods and source values |
| Crosswalk | Confirm all 63 old provinces are mapped and shares sum to one |
| Aggregation | Reconcile enterprise counts and population where source data are complete |
| Regression | Reproduce model estimates and verify sample sizes |
| Bootstrap | Reproduce point estimates and confidence intervals |
| Dashboard | Compare displayed figures with the underlying data |
| Limitations | Confirm all 12 limitations are visible |

Record the execution date, command, output and reviewer for each completed check.

## 4. Questions a judge may ask

| Question | What the team should explain |
|---|---|
| Why should an association be used to guide reform priorities? | It should be used for diagnosis and further investigation, not as causal proof. |
| Why combine historical panel evidence with PCI 2.0 benchmarking? | The frameworks differ. The relationship is conceptual and exploratory, not a direct score conversion. |
| Are the results statistically reliable? | Discuss sample size, uncertainty, multiple comparisons and sensitivity to specifications. |
| How were reform costs determined? | Explain that cost levels are team assumptions unless supported by external evidence. |
| Why use new enterprise formation as the outcome? | It is an observable indicator of local firm formation, but it does not capture all dimensions of private-sector development. |

## 5. Presentation language review

Avoid:

- "This sub-index causes more businesses to enter the market."
- "Investing in this dimension will attract more firms."
- "The model proves that the reform works."
- "This is the optimal spending priority."

Prefer:

- "This sub-index is statistically associated with the selected outcome."
- "The result identifies a dimension worth investigating further."
- "The evidence is exploratory and subject to methodological limitations."
- "The dashboard supports benchmarking rather than determining budget allocation."

## 6. Final review checklist

Before submission, the team should confirm:

- [ ] Every important number can be traced to a data source or calculation.
- [ ] All source URLs, table identifiers, units and reference periods are documented.
- [ ] All province mappings have been reviewed.
- [ ] Model estimates have been reproduced.
- [ ] Missing values are not interpreted as zero.
- [ ] Historical PCI and PCI 2.0 are clearly distinguished.
- [ ] Team assumptions are labelled.
- [ ] No unsupported causal claims remain.
- [ ] Dashboard interactions and displayed values have been tested.
- [ ] All 12 limitations are visible.
- [ ] AI assistance and human verification are disclosed.

## 7. Review status

This document defines the review requirements. It must not be treated as evidence that every check has passed.

Only mark a check as completed after the team has executed the relevant test and reviewed its output.