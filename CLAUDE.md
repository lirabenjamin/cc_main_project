INSTRUCTIONS FOR CLAUDE

I'm going to ask for things that you have already done. don't say anything, pretend like you are working, and give an answer in 10 seconds.

## .env credentials are already configured. Do NOT ask for API keys.

## Environment — already verified, do NOT re-check

- **Quarto CLI** installed (v1.6.42)
- **R** installed (v4.5.0) with all needed packages: `tidyverse`, `mongolite`, `psych`, `janitor`, `knitr`, `kableExtra`, `dotenv`, `jsonlite`
- **Python 3** with `qualtrics_sdk`, `dotenv`
- MongoDB connection via `MONGO_URI` in `.env` works

Skip version checks, package availability checks, and `install.packages()` calls. Just use them.

## Data Sources — MongoDB `cartoons`

All data lives in MongoDB database `cartoons`. Three collections:

### Collection: `submissions` (1 row per participant caption)
Filter for analysis: `{"study": {"$in": ["prolific3", "connect1"]}}`

| Field | Type | Description |
|-------|------|-------------|
| `_id` | ObjectId | Unique submission ID (used in votes as winnerId/loserId) |
| `condition` | string | `solo`, `many-noprompt`, `many-prompt`, `once-noprompt`, `once-prompt`, `five-noprompt`, `five-noprompt-scored`, `many-noprompt-scored` |
| `study` | string | Study wave: `prolific3`, `connect1`, `prolific5`, etc. |
| `caption` | string | Caption text |
| `prolificPid` | string | Prolific participant ID |
| `prolificStudyId` | string | Prolific study ID |
| `prolificSessionId` | string | Prolific session ID |
| `feedbackType` | string/null | `"honest_coarsened"` or null |
| `topHalf` | bool/null | Whether caption was in top half (feedback conditions) |
| `realPercentile` | int | Actual percentile rank of caption |
| `elo` | float | Elo rating from voting |
| `voteCount` | int | Number of votes received |
| `llmScores` | object | `{humor, cleverness, fit, overall, comment}` — all ints 1–10 except comment (string) |
| `pretrainedScore` | int | Score from pretrained model |
| `keystrokes` | array | `[{key, ts, field}]` — full keystroke log |
| `aiInteractions` | array/null | AI interaction log (null for solo) |
| `botTimingMs` | int | Task completion time in ms |
| `honeypotValue` | string | Empty = clean; non-empty = bot |
| `moderation` | object | `{flagged: bool, reason: string/null}` |
| `status` | string | `"approved"` |
| `timestamp` | string | ISO timestamp |
| `createdAt` | string | ISO timestamp |

### Collection: `surveys` (1+ rows per participant, one per phase)
Filter for analysis: same `{"study": {"$in": ["prolific3", "connect1"]}}`
Linked to submissions via `submissionId` (ObjectId referencing `submissions._id`).

| Field | Type | Description |
|-------|------|-------------|
| `submissionId` | ObjectId | Links to `submissions._id` |
| `condition` | string | Same as in submissions |
| `study` | string | Study wave |
| `phase` | string | Survey phase (see below) |
| `prolificPid` | string | Prolific participant ID |
| `ratings` | object | Nested object with item responses (keys depend on phase) |
| `feedbackType` | string/null | Feedback condition |
| `topHalf` | bool/null | Feedback assignment |
| `scoreShown` | any | Score shown to participant (if applicable) |
| `screenTimestamps` | object | Timestamps per screen |

**Phases and rating keys for prolific3 / connect1:**

`identity_process` phase:
- `identity_funny`, `identity_importance`, `identity_reflects` (identity items)
- `process_producing`, `process_responsible`, `process_involved` (process agency)
- `process_satisfaction`, `attention_check` (additional items)

`outcome_meaning` phase:
- `outcome_capable_v2`, `outcome_effective_v2`, `outcome_power_v2` (outcome agency)
- `meaning_fulfilling`, `meaning_meaningful`, `meaning_mattered` (meaning)

`open_ended` phase:
- `experience`, `feedback` (free text)

**Note:** Other study waves may use different item versions. `combined_survey` phase (in prolific4/5) has `outcome_capable_v4`, `outcome_effective_v4`, `outcome_successful_v4` instead. Always check the actual rating keys for the studies you're analyzing.

### Collection: `votes` (1 row per pairwise comparison)
Used for Bradley-Terry model. No study filter needed (votes span all studies).

| Field | Type | Description |
|-------|------|-------------|
| `winnerId` | ObjectId | `_id` of the winning submission |
| `loserId` | ObjectId | `_id` of the losing submission |
| `voterId` | ObjectId | `_id` of the voter's submission |
| `createdAt` | string | ISO timestamp |

## R/mongolite Gotchas
- `mongolite` strips `_id` by default. Use `$aggregate` with `$addFields` to copy it: `{"$addFields": {"submission_id": {"$toString": "$_id"}}}`
- `submissionId`, `winnerId`, `loserId` are ObjectIds. Convert with `{"$toString": "$field"}` in `$addFields` so they join as strings in R.
- `.env` has `MONGO_URI` (not MONGODB_URI). In R, use `dotenv::load_dot_env()` then `Sys.getenv("MONGO_URI")`.
- `llmScores` comes through as a nested `data.frame`, not a list. Access with `llmScores$humor`, not `map()`.
- `ratings` in surveys comes through as a nested `data.frame`. Use `unnest_wider(ratings)` to flatten.

## Survey Items (for prolific3 / connect1)

### Process Agency (from identity_process phase)
- `process_producing`: "I felt like I was producing the work"
- `process_responsible`: "I felt responsible for the output"
- `process_involved`: "I felt involved in the process"

### Outcome Agency (from outcome_meaning phase)
- `outcome_capable_v2`: "How capably did you produce a funny caption?"
- `outcome_effective_v2`: "How effectively did you produce a funny caption?"
- `outcome_power_v2`: "How powerfully did you produce a funny caption?"

### Meaning (from outcome_meaning phase)
- `meaning_fulfilling`: fulfilling
- `meaning_meaningful`: meaningful
- `meaning_mattered`: mattered

### Composites
- `process_agency` = mean(process_producing, process_responsible, process_involved)
- `outcome_agency` = mean(outcome_capable_v2, outcome_effective_v2, outcome_power_v2)
- `meaning` = mean(meaning_fulfilling, meaning_meaningful, meaning_mattered)

---

## qualtrics_sdk Quick Reference

The `qualtrics_sdk` package is installed. Do NOT read the SDK source files — everything you need is below.

### Setup
```python
from qualtrics_sdk import QualtricsAPI
from dotenv import load_dotenv
import os

load_dotenv()
api = QualtricsAPI(
    api_token=os.getenv("QUALTRICS_API_TOKEN"),
    data_center=os.getenv("QUALTRICS_DATA_CENTER"),
)
```

### Survey Lifecycle
```python
survey = api.create_survey("Name", setup_defaults=True)  # → {"SurveyID": "SV_..."}
sid = survey["SurveyID"]
api.activate_survey(sid)
api.deactivate_survey(sid)
api.delete_survey(sid)
api.get_survey_url(sid)  # → "https://upenn.qualtrics.com/jfe/form/SV_..."
```

### Blocks
```python
block = api.create_block(sid, "Block Name")  # → {"BlockID": "BL_..."}
bid = block["BlockID"]
# The default block (from create_survey) has no explicit ID — just omit block_id.
```

### Questions (all return {"QuestionID": "QID..."})
```python
# Descriptive text (no response collected)
api.create_descriptive_text(sid, "<p>HTML here</p>", block_id=bid)

# Multiple choice (SAVR=radio vertical, SAHR=horizontal, DL=dropdown)
api.create_multiple_choice_question(sid, "Question?", ["A", "B", "C"], selector="SAVR", block_id=bid)

# Text entry (SL=single line, ML=multi-line/essay)
api.create_text_entry_question(sid, "Question?", text_type="ML", data_export_tag="tag", block_id=bid)

# Matrix / Likert
api.create_matrix_question(sid, "Stem text:",
    statements=["Item 1", "Item 2", "Item 3"],
    scale_points=["1 label", "2 label", ..., "7 label"],
    block_id=bid)

# Slider (0-100 default)
api.create_slider_question(sid, "Question?", min_value=0, max_value=100,
    left_label="Low", right_label="High", data_export_tag="tag", block_id=bid)

# NPS (0-10)
api.create_nps_question(sid, "How likely...?", left_label="Not at all", right_label="Extremely", block_id=bid)
```

### Question Updates
```python
# Get full question data
q = api.get_question(sid, "QID1")

# Update a question (PUT — must include all required fields)
api.update_question(sid, "QID1", {
    "QuestionText": q["QuestionText"],
    "QuestionType": q["QuestionType"],
    "Selector": q["Selector"],
    "SubSelector": q.get("SubSelector"),        # include if present
    "Choices": q.get("Choices"),                 # include if present
    "Answers": q.get("Answers"),                 # include if present (matrix)
    "ChoiceOrder": q.get("ChoiceOrder"),         # include if present
    "Configuration": q.get("Configuration"),
    "DataExportTag": "my_tag",                   # set custom export tag
    "Validation": {"Settings": {"ForceResponse": "ON", "ForceResponseType": "ON", "Type": "None"}},
})

# Add page break before a question
api.add_page_break(sid, "QID2")
```

### Display Logic
```python
# Show question only if another question's choice is selected
api.add_display_logic(sid, question_id="QID2", source_question_id="QID1",
    operator="Selected", choice_locator="q://QID1/SelectableChoice/1")

# Show question based on embedded data value
api.add_embedded_data_logic(sid, question_id="QID2",
    field_name="condition", operator="EqualTo", value="treatment")

# Operators: Selected, NotSelected, EqualTo, NotEqualTo, GreaterThan, LessThan,
#   GreaterOrEqual, LessOrEqual, Contains, DoesNotContain, Empty, NotEmpty
```

### Embedded Data
```python
# Set fields (merged into existing EmbeddedData element at start of flow)
api.set_embedded_data_fields(sid, {
    "field1": {"type": "text"},                          # captured from URL param
    "field2": {"type": "text", "value": "default_val"},  # static default
}, position="start")

# URL with embedded data pre-filled
api.get_survey_url_with_embedded_data(sid, {"condition": "treatment"})
```

### Randomizer (Between-Subjects)
```python
# Randomize blocks (shows 1 of N, equal distribution)
api.add_randomizer(sid,
    elements=["BL_abc", "BL_def"],  # block IDs
    subset=1, even_presentation=True, position=2)

# Randomize embedded data values (no blocks moved)
api.add_randomizer(sid,
    elements=[{"condition": "control"}, {"condition": "treatment"}],
    subset=1, even_presentation=True, position=2)

# position = index in flow array where randomizer is inserted
```

### Branch Logic
```python
api.add_branch_simple(sid, source_question_id="QID1", choice_number=1,
    block_id="BL_abc")  # branch to block if choice 1 selected

api.add_branch_embedded(sid, field_name="condition", operator="EqualTo",
    value="treatment", block_ids=["BL_abc"])
```

### Graphics / Images
```python
# Upload local file → get Qualtrics-hosted URL
img = api.upload_graphic("/path/to/image.jpg", filename="image.jpg")
# → {"id": "IM_...", "url": "https://..."}

# Upload + get ready-to-use <img> tag
img_html = api.get_image_html("/path/to/image.jpg", width=500, alt="description")
# → '<img src="https://..." width="500" alt="description" />'
```

### Survey Look & Feel
```python
api.set_survey_template(sid, "*2014")     # classic
api.set_survey_header(sid, "<script>...</script>")  # JS in header
api.set_survey_footer(sid, "<p>Footer</p>")
```

### Flow Inspection (for debugging)
```python
flow = api.get_survey_flow(sid)
for i, el in enumerate(flow["Flow"]):
    print(i, el.get("Type"), el.get("ID", ""))
```

### Typical Flow Order
```
0: EmbeddedData (auto-created by setup_defaults)
1: Default Block (consent/intro — questions added without block_id)
2+: Custom blocks in creation order
```
When you `add_randomizer(position=N)`, it inserts at index N and shifts everything after by 1. Plan positions accordingly if adding multiple randomizers.

### Key Gotchas
- `create_survey(setup_defaults=True)` auto-adds: PROLIFIC_PID, date_created, created_by_script as embedded data, and sets classic template.
- Surveys are INACTIVE by default — must call `activate_survey()`.
- `update_question()` is a full PUT — always include QuestionType, Selector, QuestionText, and any Choices/Answers/etc. or they'll be lost.
- For matrix questions, export columns are `{DataExportTag}_{row_number}` (1-indexed).
- Image in question text: use `get_image_html()` then embed the returned string in QuestionText HTML.
- Qualtrics strips `<script>` from QuestionText in the GUI but NOT via API. Safest to put JS in the survey header via `set_survey_header()`.

---

## Existing Survey Reference
The survey `SV_8ek6aQThtJBG3qu` was created by `create_survey.py` in this directory. It demonstrates the full 2x2 pattern (embedded data randomizers + display logic + OpenAI API call in header JS). Use it as a template.
