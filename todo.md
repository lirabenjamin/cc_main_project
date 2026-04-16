# Todo — Caption Contest 2x2 Demo

## Completed
- [x] Create 2x2 Qualtrics survey v1 (AI assistance x Feedback valence)
  - Survey ID: `SV_8ek6aQThtJBG3qu`
  - Preview: https://upenn.qualtrics.com/jfe/form/SV_8ek6aQThtJBG3qu
  - Edit: https://upenn.qualtrics.com/survey-builder/SV_8ek6aQThtJBG3qu/edit
- [x] Create 2x2 Qualtrics survey v2 (2025-04-15)
  - Survey ID: `SV_eXWikVMLoLLKa9w`
  - Preview: https://upenn.qualtrics.com/jfe/form/SV_eXWikVMLoLLKa9w
  - Edit: https://upenn.qualtrics.com/survey-builder/SV_eXWikVMLoLLKa9w/edit

## Completed
- [x] Write `clean_data.qmd` — data cleaning pipeline with codebook, composites, alphas (2026-04-15)
  - Downloads raw data via `download_raw_data.R` → 3 RDS files
  - Merges submissions + 3 survey phases → 1 row per person (182 rows × 43 cols)
  - Codebook table, Cronbach's alphas for 4 composites, descriptive stats
  - Exports `data_clean.csv`

- [x] Write `results.qmd` — methods & results with condition comparisons, inline stats, figures (2026-04-15)
  - Methods: participants, procedure, measures
  - Results: descriptive stats table, Welch t-tests with Cohen's d, narrative writeup with inline R stats
  - Figures: survey composites bar chart, caption quality bar chart
  - Renders to `results.html`

## To verify (BenBen) — QMD
- [ ] Review codebook and variable naming in `clean_data.qmd`
- [ ] Review condition labels: renamed `many-noprompt` → `ai` — confirm this is correct
- [ ] 29 of 182 participants have no survey data — expected?
- [ ] 1 survey submission_id doesn't match any submission — investigate?

## To verify (BenBen) — Survey
- [ ] Preview survey v2 — walk through all 4 conditions:
  - Control + Positive: `?ai_condition=control&feedback_condition=positive`
  - Control + Negative: `?ai_condition=control&feedback_condition=negative`
  - AI + Positive: `?ai_condition=ai&feedback_condition=positive`
  - AI + Negative: `?ai_condition=ai&feedback_condition=negative`
- [ ] Confirm AI "Get Caption" button calls OpenAI and returns a caption
- [ ] Confirm display logic hides AI button in control, shows correct feedback text
- [ ] Confirm all scales render with correct anchors
