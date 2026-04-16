#!/usr/bin/env python3
"""
Caption Contest 2x2 Demo — Qualtrics Survey Builder
Design: AI Assistance (control | ai) x Feedback (positive | negative)
"""

import os
from dotenv import load_dotenv
from qualtrics_sdk import QualtricsAPI

load_dotenv()

api = QualtricsAPI(
    api_token=os.getenv("QUALTRICS_API_TOKEN"),
    data_center=os.getenv("QUALTRICS_DATA_CENTER"),
)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ── Helpers ──────────────────────────────────────────────────────────────────

def update_q(survey_id, qid, tag=None, force=False):
    """Set DataExportTag and/or ForceResponse on an existing question."""
    q = api.get_question(survey_id, qid)
    data = {
        "QuestionText": q["QuestionText"],
        "QuestionType": q["QuestionType"],
        "Selector": q["Selector"],
    }
    for k in ("SubSelector", "Choices", "Answers", "ChoiceOrder",
              "Configuration", "DisplayLogic", "ColumnLabels"):
        if q.get(k):
            data[k] = q[k]

    data["DataExportTag"] = tag if tag else q.get("DataExportTag", f"Q{qid}")

    if force:
        data["Validation"] = {
            "Settings": {"ForceResponse": "ON",
                         "ForceResponseType": "ON",
                         "Type": "None"}
        }
    elif q.get("Validation"):
        data["Validation"] = q["Validation"]

    api.update_question(survey_id, qid, data)


# ── 1. Create survey ────────────────────────────────────────────────────────

survey = api.create_survey("Caption Contest 2x2 Demo")
sid = survey["SurveyID"]
print(f"Survey created: {sid}")

# ── 2. Upload image ─────────────────────────────────────────────────────────

img = api.upload_graphic(
    os.path.join(SCRIPT_DIR, "penguins.jpg.jpg"),
    filename="penguins.jpg",
)
img_tag = f'<img src="{img["url"]}" width="500" alt="Cartoon: penguins in a city" />'
print("Image uploaded")

# ── 3. Embedded data for condition tracking ──────────────────────────────────

api.set_embedded_data_fields(sid, {
    "ai_condition": {"type": "text"},
    "feedback_condition": {"type": "text"},
})
print("Embedded data configured")

# ── 4. JavaScript for AI caption button (survey header) ─────────────────────

header_js = """<script>
function generateCaption(btn) {
  btn.disabled = true;
  btn.textContent = "Generating...";
  var rd = btn.parentElement.querySelector(".ai-result");
  rd.style.display = "block";
  rd.innerHTML = "<em>Thinking...</em>";
  fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer """ + OPENAI_API_KEY + """"
    },
    body: JSON.stringify({
      model: "gpt-4o-mini",
      messages: [{
        role: "user",
        content: "Write one funny caption for a New Yorker cartoon showing a city street completely filled with penguins, two confused people walking among them, and a lone pigeon. Dry wit, one sentence. Output only the caption text."
      }],
      max_tokens: 60
    })
  })
  .then(function(r) { return r.json(); })
  .then(function(d) {
    rd.innerHTML = '<strong>AI Suggestion:</strong> "' +
      d.choices[0].message.content.trim().replace(/^"|"$/g, "") + '"';
    btn.textContent = "Caption Generated";
    btn.style.background = "#388E3C";
  })
  .catch(function() {
    rd.innerHTML = "<em>Could not generate caption. Please write your own!</em>";
    btn.disabled = false;
    btn.textContent = "Try Again";
  });
}
</script>"""
api.set_survey_header(sid, header_js)
print("AI JavaScript added to header")

# ── 5. Consent block (uses default block) ────────────────────────────────────

api.create_descriptive_text(sid,
    "<h2>Consent to Participate</h2>"
    "<p>You are invited to participate in a brief study about humor and creativity. "
    "You will view a cartoon and write a funny caption, then answer a few "
    "questions about your experience.</p>"
    "<p>Participation is voluntary and responses are confidential.</p>")

consent_q = api.create_multiple_choice_question(sid,
    "Do you consent to participate?",
    ["I agree to participate"])
update_q(sid, consent_q["QuestionID"], tag="consent", force=True)
print("Consent block ready")

# ── 6. Caption Task block ───────────────────────────────────────────────────

cb = api.create_block(sid, "Caption Task")["BlockID"]

api.create_descriptive_text(sid,
    f'<div style="text-align:center">{img_tag}'
    '<p style="font-style:italic;color:#666">Cartoon by Meredith</p></div>',
    block_id=cb)

ai_help = api.create_descriptive_text(sid,
    '<div style="text-align:center;margin:15px 0">'
    '<p>Need help? Click below to get an AI-generated caption suggestion.</p>'
    '<button onclick="generateCaption(this)" '
    'style="padding:12px 24px;font-size:16px;background:#4A90D9;color:#fff;'
    'border:none;border-radius:6px;cursor:pointer;font-weight:bold">'
    'Get AI Caption</button>'
    '<div class="ai-result" style="display:none;margin-top:15px;padding:15px;'
    'background:#f0f7ff;border:1px solid #b8d4f0;border-radius:8px;'
    'font-size:15px"></div></div>',
    block_id=cb)
ai_qid = ai_help["QuestionID"]

caption = api.create_text_entry_question(sid,
    "Write a funny caption for this cartoon:",
    text_type="ML", data_export_tag="caption", block_id=cb)
update_q(sid, caption["QuestionID"], tag="caption", force=True)
print(f"Caption task block: {cb}")

# ── 7. Process Agency block ──────────────────────────────────────────────────

pa = api.create_block(sid, "Process Agency")["BlockID"]

pa_q = api.create_matrix_question(sid,
    "Please indicate how much you agree or disagree with each statement:",
    statements=[
        "I felt like I was producing the work",
        "I felt responsible for the output",
        "I felt involved in the process",
    ],
    scale_points=[
        "Strongly Disagree", "Disagree", "Somewhat Disagree",
        "Neither Agree nor Disagree",
        "Somewhat Agree", "Agree", "Strongly Agree",
    ],
    block_id=pa)
update_q(sid, pa_q["QuestionID"], tag="process_agency", force=True)
print(f"Process agency block: {pa}")

# ── 8. Feedback block ───────────────────────────────────────────────────────

fb = api.create_block(sid, "Feedback")["BlockID"]

pos = api.create_descriptive_text(sid,
    '<div style="padding:20px;background:#e8f5e9;border:1px solid #4caf50;'
    'border-radius:8px;text-align:center">'
    '<h3 style="color:#2e7d32">Great news!</h3>'
    '<p style="font-size:16px">A panel of judges rated your caption as '
    '<strong>funny</strong>. Nice work!</p></div>',
    block_id=fb)

neg = api.create_descriptive_text(sid,
    '<div style="padding:20px;background:#fbe9e7;border:1px solid #ef5350;'
    'border-radius:8px;text-align:center">'
    '<h3 style="color:#c62828">Results</h3>'
    '<p style="font-size:16px">A panel of judges reviewed your caption and '
    'rated it as <strong>not funny</strong>.</p></div>',
    block_id=fb)
print(f"Feedback block: {fb}")

# ── 9. Outcome Agency block ─────────────────────────────────────────────────

oa = api.create_block(sid, "Outcome Agency")["BlockID"]

oa_q = api.create_matrix_question(sid,
    "Please rate the following:",
    statements=[
        "How capably did you produce a funny caption?",
        "How effectively did you produce a funny caption?",
        "How successfully did you produce a funny caption?",
    ],
    scale_points=[
        "Not at all", "Slightly", "Somewhat",
        "Moderately", "Quite", "Very", "Extremely",
    ],
    block_id=oa)
update_q(sid, oa_q["QuestionID"], tag="outcome_agency", force=True)
print(f"Outcome agency block: {oa}")

# ── 10. Meaning block ───────────────────────────────────────────────────────

mb = api.create_block(sid, "Meaning")["BlockID"]

m_q = api.create_matrix_question(sid,
    "To what extent did the caption-writing task feel...",
    statements=["fulfilling", "meaningful", "like it mattered"],
    scale_points=[
        "Not at all", "Slightly", "Somewhat",
        "Moderately", "Quite", "Very", "Extremely",
    ],
    block_id=mb)
update_q(sid, m_q["QuestionID"], tag="meaning", force=True)
print(f"Meaning block: {mb}")

# ── 11. Demographics block ──────────────────────────────────────────────────

db = api.create_block(sid, "Demographics")["BlockID"]

api.create_text_entry_question(sid,
    "What is your age?", text_type="SL",
    data_export_tag="age", block_id=db)

api.create_multiple_choice_question(sid,
    "What is your gender?",
    ["Man", "Woman", "Non-binary", "Prefer not to say"],
    block_id=db)

api.create_multiple_choice_question(sid,
    "How often do you use AI tools like ChatGPT?",
    ["Never", "Rarely", "Sometimes", "Often", "Daily"],
    block_id=db)
print(f"Demographics block: {db}")

# ── 12. Display logic ───────────────────────────────────────────────────────

api.add_embedded_data_logic(sid, ai_qid,
    "ai_condition", "EqualTo", "ai")
api.add_embedded_data_logic(sid, pos["QuestionID"],
    "feedback_condition", "EqualTo", "positive")
api.add_embedded_data_logic(sid, neg["QuestionID"],
    "feedback_condition", "EqualTo", "negative")
print("Display logic configured")

# ── 13. Randomizers ─────────────────────────────────────────────────────────
# Flow before randomizers:
#   0: EmbeddedData | 1: Consent | 2: Caption | 3: Process Agency
#   4: Feedback     | 5: Outcome | 6: Meaning | 7: Demographics

api.add_randomizer(sid,
    elements=[{"ai_condition": "control"}, {"ai_condition": "ai"}],
    subset=1, even_presentation=True, position=2)
print("Randomizer 1 (AI condition) added")

# After R1 insert the flow shifted +1 starting at index 2:
#   ... | 2: R1 | 3: Caption | 4: Process | 5: Feedback | ...
api.add_randomizer(sid,
    elements=[{"feedback_condition": "positive"},
              {"feedback_condition": "negative"}],
    subset=1, even_presentation=True, position=5)
print("Randomizer 2 (Feedback condition) added")

# ── 14. Activate ────────────────────────────────────────────────────────────

api.activate_survey(sid)

# ── Output ───────────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print(f"  Survey ID : {sid}")
print(f"  Preview   : {api.get_survey_url(sid)}")
print(f"  Edit      : https://{api.data_center}/survey-builder/{sid}/edit")
print("=" * 60)

print("\nExport tag mapping:")
print("  process_agency_1  ->  I felt like I was producing the work")
print("  process_agency_2  ->  I felt responsible for the output")
print("  process_agency_3  ->  I felt involved in the process")
print("  outcome_agency_1  ->  How capably did you produce a funny caption?")
print("  outcome_agency_2  ->  How effectively did you produce a funny caption?")
print("  outcome_agency_3  ->  How successfully did you produce a funny caption?")
print("  meaning_1         ->  fulfilling")
print("  meaning_2         ->  meaningful")
print("  meaning_3         ->  like it mattered")
print("\nNote: OpenAI API key is in the survey header JS (visible in page source).")
