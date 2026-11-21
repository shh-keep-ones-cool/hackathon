# Project rules

## Reader and decision
The reader is a research/case-competition jury and a policy-oriented business reader. The dashboard helps the reader identify which dimensions of perceived provincial governance are relatively stronger/weaker and how those dimensions are associated with business formation and enterprise density; it does not rank provinces by an unpublished PCI total or recommend a causal policy intervention.

## Question (exact English wording)
**How are perceived provincial governance conditions associated with private-sector business formation and business density across Vietnam's 34 provinces in 2025?**

## File roles
- `data/pci_provinces.csv`: primary 2025 PCI component input plus GSO outcomes when verified; `pci_total` is blank unless VCCI publishes it.
- `data/pci_bpi_2025.csv`: separate BPI 2025 input; never treat BPI as a PCI subindex.
- `data/pci_panel_63.csv`: legacy PCI input; year-specific framework and source column mapping required.
- `data/outcomes_panel_63.csv`: old-province GSO outcomes input.
- `data/crosswalk_63_to_34.csv`: official old-to-new geography bridge; check shares sum to one.
- `data/pci_concordance.csv`: conceptual index bridge; metadata only, not an input for transforming scores.
- `data/pci_subindex_meta.csv`: display metadata; `horizon_years` and `cost_level` are team assumptions.
- `data/vn_provinces.geojson`: mapping geometry; join only by `province_id`.
- `data/model_results.csv`, `data/derived_features_2025.csv`, `data/outcomes_panel_34.csv`: Python-generated outputs; never edit manually.
- `checks.md`: verification targets only; never load as model inputs.
- `README.md`: source registry, unit dictionary and limitations.

## Computation rules
- Never hard-code calculated rates, logs, z-scores, standardized values, ranks or model coefficients into raw CSV inputs.
- Python performs ingestion, validation, normalization, crosswalk aggregation, feature engineering and OLS. The browser JavaScript may calculate display summaries and a simple OLS parity check only from loaded CSV data; it must not silently replace a missing source value.
- `pop` is stored in thousand persons. `firms_new_per_1000 = firms_new / pop`; verify this dimensional conversion.
- Aggregate enterprise counts and population by multiplying old-province values by `share` and summing. Aggregate `grdp_pc` as a population-weighted average; never sum per-capita GRDP.
- Run separate single-subindex OLS models because n≤34. Show n, coefficient, 95% CI, p-value and R². Use “association”, not “effect”.
- Use complete cases only and report the actual n per model/chart. Blank is not zero.
- Do not merge PCI legacy scores and PCI 2.0 scores as if they are identical. Use `pci_concordance.csv` for labelled conceptual discussion only.
- Any change in source, mapping or formula must be reflected in `README.md` and `docs/AI_USE.md`.

## Language rules
- No causal wording: avoid “causes”, “drives”, “impact of PCI on…”, “leads to”. Prefer “is associated with”, “co-varies with”, “descriptive pattern”.
- Always show n and the year/coverage window.
- State whether each GRDP measure is current-price or constant-price.
- Label `horizon_years` and `cost_level` as **“Giả định của nhóm”** wherever displayed.
- Do not call BPI “PCI total”.

## Design rules
- One-screen-first: headline and one-sentence finding before charts.
- Put a source line under every chart/table.
- Do not use colour alone to encode category; include text labels.
- Peer averages exclude the selected province (leave-one-out mean).
- Do not create a rank order for 2025 PCI total score; no comparable total/rank is published on the public PCI 2.0 page.
- Show 34 province coverage and complete-case n; show missing values as “Chưa có dữ liệu”, never zero.
- Maps use `province_id` only; map geometry must be the 2025 34-province version.

## Workflow
1. Plan and inspect files first; state the specific stage and expected output.
2. Work one stage at a time: source retrieval → raw import → validation → harmonization → analysis → dashboard.
3. Stop after each stage for a human review before changing the next stage.
4. Never overwrite original raw downloads; put them in `data/raw/` (gitignored).
5. Commit after each working stage with a descriptive message.
6. Update `docs/AI_USE.md` after each stage with the tool, AI contribution, human checks, owner and date.
7. If source layouts change, stop and request a reviewed mapping; do not guess column meanings.

## Known traps
- PCI is a business survey/perception index, not a direct objective audit.
- Cross-section n is at most 34; models can be unstable.
- Reverse causality/endogeneity is possible.
- Reform effects may be delayed; horizon values are assumptions.
- PCI 2.0 in 2025 is a framework break versus legacy PCI.
- Province mergers reduce geographic variation; never sum index scores across old provinces.
- Crosswalk is a geography bridge, not a PCI score bridge.
- GRDP current-price and constant-price values are not interchangeable.
- GSO enterprise definitions and reference dates may vary by table/year.
- `pci_concordance.csv` is approximate; no cardinal equivalence.
- `cost_level` and `horizon_years` are assumptions, not observed facts.
- BPI is a separate experimental 2025 measure only.
- VCCI's raw dataset citation and redistribution conditions must be respected.
