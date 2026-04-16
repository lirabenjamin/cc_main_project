# Comms

## 2026-04-15 15:30 — QMD cleaning pipeline: assumptions to verify

BenBen, I wrote `clean_data.qmd`. A few assumptions I need you to check:

1. **Linking Qualtrics ↔ MongoDB:** I assumed MongoDB `submissions` will have a `participantId` field that matches either `PROLIFIC_PID` or Qualtrics `ResponseId`. Is that correct, or is the linking done differently?

2. **Votes schema:** I assumed `votes` has `winner_id` and `loser_id` columns referencing submission `_id`s. If the fields are named differently (e.g., `chosen`, `rejected`, or nested), let me know.

3. **Qualtrics numeric coding:** The `qualtRics` package sometimes returns Likert items as labeled text ("Strongly Disagree") rather than integers (1–7). I cast with `as.integer()` which will work if Qualtrics exports numeric recodes. If it exports labels, I'll need to add a recode step. Want me to handle both cases?

4. **Bradley-Terry reference level:** BT estimates are relative — one caption is fixed at 0. Currently I'm using the default (alphabetically first `_id`). Should I anchor on the seed captions instead?

5. **Survey ID:** I pointed the QMD at the new survey `SV_eXWikVMLoLLKa9w`. Confirm that's the one you'll collect data with (not the earlier `SV_8ek6aQThtJBG3qu`).

---

## 2026-04-15 — Survey v2 created

New survey instance created from `create_survey.py`.

**Survey:** `SV_eXWikVMLoLLKa9w`
- Preview: https://upenn.qualtrics.com/jfe/form/SV_eXWikVMLoLLKa9w
- Edit: https://upenn.qualtrics.com/survey-builder/SV_eXWikVMLoLLKa9w/edit

---

## 2026-04-15 — Survey created

BenBen, the 2x2 Caption Contest survey is live on Qualtrics. Here's what you need to know:

**Survey:** `SV_8ek6aQThtJBG3qu`
- Preview: https://upenn.qualtrics.com/jfe/form/SV_8ek6aQThtJBG3qu
- Edit: https://upenn.qualtrics.com/survey-builder/SV_8ek6aQThtJBG3qu/edit

**Design:** AI Assistance (control | ai) x Feedback (positive | negative), both randomized via embedded data with even presentation.

**One thing to know:** Your OpenAI API key is embedded in the survey header JavaScript (visible in page source). Fine for a teaching demo, but rotate the key after if you're concerned about exposure.

**To test all 4 cells**, append these to the preview URL:
- `?ai_condition=control&feedback_condition=positive`
- `?ai_condition=control&feedback_condition=negative`
- `?ai_condition=ai&feedback_condition=positive`
- `?ai_condition=ai&feedback_condition=negative`

No questions for you right now — just verify it looks right in the preview.
