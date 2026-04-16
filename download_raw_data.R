#!/usr/bin/env Rscript
# download_raw_data.R
# Pull raw data from MongoDB (cartoons db) and save as RDS files.
# Run this once before rendering clean_data.qmd.
# ──────────────────────────────────────────────────────────────────────────────

library(mongolite)
library(jsonlite)
dotenv::load_dot_env()

uri <- Sys.getenv("MONGO_URI")
stopifnot(nzchar(uri))

STUDY_FILTER <- '{"study": {"$in": ["prolific3", "connect1"]}}'

# ── Submissions ──────────────────────────────────────────────────────────────
cat("Downloading submissions...\n")
sub_con <- mongo(collection = "submissions", db = "cartoons", url = uri)

submissions_raw <- sub_con$aggregate(paste0('[
  {"$match": ', STUDY_FILTER, '},
  {"$addFields": {
    "submission_id": {"$toString": "$_id"},
    "n_keystrokes":  {"$size": {"$ifNull": ["$keystrokes", []]}},
    "n_tab_leaves":  {"$size": {"$ifNull": ["$tabLeaves", []]}},
    "n_ai_interactions": {"$size": {"$ifNull": ["$aiInteractions", []]}}
  }},
  {"$project": {
    "submission_id": 1,
    "study": 1,
    "condition": 1,
    "sample": 1,
    "caption": 1,
    "prolificPid": 1,
    "feedbackType": 1,
    "topHalf": 1,
    "realPercentile": 1,
    "elo": 1,
    "voteCount": 1,
    "llmScores": 1,
    "pretrainedScore": 1,
    "botTimingMs": 1,
    "honeypotValue": 1,
    "moderation": 1,
    "n_keystrokes": 1,
    "n_tab_leaves": 1,
    "n_ai_interactions": 1,
    "timestamp": 1,
    "createdAt": 1,
    "_id": 0
  }}
]'))

cat(sprintf("  → %d submissions downloaded\n", nrow(submissions_raw)))
sub_con$disconnect()

# ── Surveys ──────────────────────────────────────────────────────────────────
cat("Downloading surveys...\n")
sur_con <- mongo(collection = "surveys", db = "cartoons", url = uri)

surveys_raw <- sur_con$aggregate(paste0('[
  {"$match": ', STUDY_FILTER, '},
  {"$addFields": {
    "submission_id_str": {"$toString": "$submissionId"}
  }},
  {"$project": {
    "submission_id_str": 1,
    "study": 1,
    "condition": 1,
    "phase": 1,
    "prolificPid": 1,
    "ratings": 1,
    "feedbackType": 1,
    "topHalf": 1,
    "scoreShown": 1,
    "_id": 0
  }}
]'))

cat(sprintf("  → %d survey rows downloaded\n", nrow(surveys_raw)))
sur_con$disconnect()

# ── Votes ────────────────────────────────────────────────────────────────────
cat("Downloading votes...\n")
vot_con <- mongo(collection = "votes", db = "cartoons", url = uri)

votes_raw <- vot_con$aggregate('[
  {"$addFields": {
    "winner_id": {"$toString": "$winnerId"},
    "loser_id":  {"$toString": "$loserId"},
    "voter_id":  {"$toString": "$voterId"}
  }},
  {"$project": {
    "winner_id": 1,
    "loser_id": 1,
    "voter_id": 1,
    "createdAt": 1,
    "_id": 0
  }}
]')

cat(sprintf("  → %d votes downloaded\n", nrow(votes_raw)))
vot_con$disconnect()

# ── Save ─────────────────────────────────────────────────────────────────────
saveRDS(submissions_raw, "raw_submissions.rds")
saveRDS(surveys_raw,     "raw_surveys.rds")
saveRDS(votes_raw,       "raw_votes.rds")

cat("Saved: raw_submissions.rds, raw_surveys.rds, raw_votes.rds\n")
cat("Done.\n")
