Here’s a **clear, finalized tech stack and directory structure** for your **Federated Natural Language Query System with MongoDB Cluster + Gemini API (Hybrid Approach)**.

---

## **Tech Stack**

### **Core Components**

1. **Backend Framework:** Flask (lightweight, Python-based, easy to deploy)
2. **Database:** MongoDB Atlas (Cluster with 4 databases → each having multiple collections)
3. **ETL/Integration:** Python scripts (custom ETL pipeline for connecting & normalizing data)
4. **Query Generation:** Gemini API (LLM for converting natural language → MongoDB queries)
5. **Response Formatting:** JSON output for each query (to be stored in `/results/`)

### **Optional / Future Add-ons**

- **Frontend (Phase 2):** React or Next.js (not for now)
- **Authentication:** JWT (future)
- **Deployment:** Render / Railway / Vercel (for Flask backend)

---

## **Project Directory Structure**

```
Backend/
├── src/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # Entry point (FastAPI app)
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── query_routes.py    # Query execution routes
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── db_service.py      # Database service (query execution)
│   │   │   ├── federation_service.py  # Federation orchestration
│   │   │   ├── plan_builder.py    # Build execution plans
│   │   │   ├── adapters.py        # Database adapters (Postgres/MySQL/etc.)
│   │   ├── nlp/
│   │   │   ├── __init__.py
│   │   │   ├── parser_rule_based.py   # Existing rule-based parser
│   │   │   ├── llm_query_generator.py # NEW: LLM-based query generation
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── config.py          # Configs (API keys, DB URLs)
│   │   │   └── text_utils.py      # Text preprocessing helpers
│   ├── io_utils/
│   │   ├── __init__.py
│   │   └── write_json.py          # Exporting query results
│   ├── llm_models/                # NEW: Optional LLM helper scripts
│   │   ├── __init__.py
│   │   ├── openai_connector.py    # LLM API integration (OpenAI, Gemini, etc.)
│   │   └── prompt_templates.py    # Store reusable prompt templates
├── results/                       # Query outputs (JSON/CSV)
├── scripts/
│   └── run_query.py               # CLI script for testing queries
├── .env                           # Environment variables (LLM keys, DB creds)
├── requirements.txt               # Dependencies
└── README.md                      # Project overview

```

```
Backend/
  src/
    app/
      __init__.py
      main.py
      routes/
        __init__.py
        query_routes.py
      services/
        __init__.py
        db_service.py
        federation_service.py
        plan_builder.py
        adapters.py
      nlp/
        __init__.py
        parser_rule_based.py
      utils/
        __init__.py
        config.py
        text_utils.py
    io_utils/
      __init__.py
      write_json.py
  results/
  scripts/
    run_query.py
  .env
  requirements.txt
```

---

## **Why this structure?**

- **Separation of concerns:** LLM handling, database interaction, and federation logic are modular.
- **Scalable:** Can easily add new databases or query templates.
- **Production-ready:** Works with MongoDB Atlas cluster directly.
- **Hybrid approach:** Gemini handles query generation, Python executes & federates.

---

### **Tech Flow (Step-by-step high level)**

1. **User submits query** (e.g., _“Get average sales in last 3 months for all stores”_)
2. **Flask route receives it** → passes to `llm_service.py`
3. **LLM converts query → JSON MongoDB queries per database**
4. **db_service.py connects to MongoDB cluster** → executes each query
5. **federation_service.py aggregates results** (if needed)
6. **Stores the final result in `/results/query_results.json`**
7. **Returns JSON response to user**

---

Would you like me to now:

1. **Create this exact directory structure with empty boilerplate files** so you can start coding,
   OR
2. **Explain each module in depth first (what code will go inside each)?**

Which path should we take next?

# high-level architecture

**input:** natural language query
**engine:** hybrid planner (rule-based first → gemini fallback), per-source query builders, federated executor, normalizer, ranker
**data:** mongodb atlas cluster (4 databases, one per provider)
**output:** unified JSON file + API response

```
user → /query (flask API) → parser → planner → per-source queries
   → federated execution (parallel) → normalize → merge/rank/dedup
   → write output JSON (timestamped) → return response
```

---

# data layout (mongodb atlas)

you said you’ll keep **4 databases inside one atlas project**. good. inside each DB, create a single collection `courses` (or keep the original name—your call). recommend:

- `db_coursera.courses`
- `db_futurelearn.courses`
- `db_simplilearn.courses`
- `db_udacity.courses`

## raw → curated (ETL)

don’t write directly to `courses`. do ELT:

- `*_raw` (land raw rows exactly as scraped)
- `*_curated` (cleaned, normalized types, enriched fields)
- `courses` (a view or a collection you query in prod)

**why:** keeps ingestion clean, repeatable, auditable.

### curated document shape (canonical superset)

```json
{
  "_id": "...",
  "platform": "Coursera|FutureLearn|Simplilearn|Udacity",
  "title": "Machine Learning Specialization",
  "url": "https://...",
  "category": "Data Science",
  "subCategory": "Machine Learning",
  "courseType": "Specialization|Free Course|University Program|...",
  "language": "English",
  "subtitleLanguages": ["English", "Arabic", "..."],

  "skills": ["Python Programming", "Pandas", "Numpy"],
  "instructors": ["Andrew Ng", "Eddy Shyu", "..."],

  "ratingText": "4.9stars",        // raw string kept for lineage
  "rating": 4.9,                    // float parsed or null

  "numViewersText": "10,438",       // raw
  "numViewers": 10438,              // int parsed or null

  "durationText": "Approximately 3 months to complete",
  "durationDays": 90,               // int approx or null

  // provider-specific long text fields merged for search & snippet
  "shortIntro": "...",
  "whatYouLearn": "...",
  "topics": ["AI & Robotics", "Python", "CRM", ...], // FL topics split
  "prerequisites": "text if present",

  // denormalized search field (for Atlas Search & fallback regex)
  "searchIndex": "title + skills + shortIntro + whatYouLearn + topics + category + subCategory",

  // lineage
  "source": { "db":"db_coursera_raw", "rowId":"..." },
  "ingestedAt": "2025-08-23T16:30:00Z",
  "curatedAt": "2025-08-23T16:32:00Z",
  "version": 1
}
```

> keep both **raw** and **parsed** fields so you can fix parsers later without losing source signal.

## indexes

create per-collection indexes:

- `{ title: "text", skills: "text", category: 1 }` (fallback)
- `{ rating: -1 }`
- `{ durationDays: 1 }`
- `{ platform: 1 }`

**if using Atlas Search (recommended):** create an **analyzer** and index on:

- `title`, `skills`, `shortIntro`, `whatYouLearn`, `topics`, `category`, `subCategory`, `searchIndex`
- add a `dynamic` true, plus `folding` analyzer for case/diacritics
- you’ll query with `$search` + `compound` + `phrase`/`text` operators

---

# repository layout

```
federated_nlq/
  README.md
  pyproject.toml            # poetry/pip-tools; pin deps
  .env.example

  src/
    app/                    # Flask API
      __init__.py
      server.py             # create_app(), routes
      routes_query.py       # POST /query
      routes_debug.py       # GET /health, GET /last
      middleware.py
      schemas.py            # pydantic-like request/response validation

    config/
      settings.py           # env (Mongo URI, DB names, Gemini key)
      providers.py          # db/collection names, capabilities
      synonyms.py           # top/best/less important mappings etc.
      canonical_model.py    # target response keys & types

    db/
      mongo.py              # client factory, helpers
      indexes.py            # build indexes & atlas search specs

    etl/
      ingest_raw/
        load_coursera.py
        load_futurelearn.py
        load_simplilearn.py
        load_udacity.py
      curate/
        normalize_common.py # parsing utilities (rating, duration, skills)
        transform_coursera.py
        transform_futurelearn.py
        transform_simplilearn.py
        transform_udacity.py
      publish/
        upsert_courses.py   # write to *_curated / courses
      jobs.py               # orchestrate: raw -> curated -> courses

    nlp/
      parser_rule_based.py  # intent/entity extractor
      entity_extractors.py  # topic, platform, limits, filters
      intent.py             # rank vs filter vs explore
      plan_builder.py       # build per-source QueryPlan
      llm_gemini.py         # fallback query synthesis (Mongo JSON)
      prompts/
        mongo_query_gen.txt
        disallowed_ops.txt

    federation/
      executors.py          # parallel query runner
      query_templates.py    # Mongo aggregation builders
      adapters.py           # per-source field mapping to canonical
      merge_rank.py         # dedupe, global rank, ties

    io/
      write_json.py         # save to output/responses/*.json
      file_paths.py
      logging_conf.py

    utils/
      text.py               # cleaning, tokenization
      timeparse.py          # “3 months” → 90 days
      ratingparse.py        # "4.9stars" → 4.9
      numbers.py

  tests/
    unit/
    integration/
    data/
      samples/*.json

  scripts/
    init_db.py              # build dbs/collections/indexes
    run_etl_sample.sh
    run_server.sh

  output/
    responses/
    debug/
    logs/
```

---

# execution flow (runtime)

1. **POST /query** with body:

   ```json
   { "query": "Show me top 5 courses in Data Science from Coursera" }
   ```

2. `parser_rule_based`:

   - intent: RANK
   - topic: "Data Science"
   - platform: "Coursera"
   - limit: 5
   - sort: rating DESC (via synonyms)

3. `plan_builder`:

   - scopes to `db_coursera.courses`
   - builds a Mongo aggregation:

     - `$search` (if Atlas Search) on `searchIndex` with `"data science"`
     - OR `$or: [ {title: /data science/i}, {skills: /data science/i}, ...]`
     - `$sort: { rating: -1 }`
     - `$limit: 5`

4. `federation.executors`:

   - runs the per-source queries in parallel (here only 1)

5. `adapters`:

   - map provider doc → canonical model

6. `merge_rank`:

   - dedupe by `url`
   - global sort if multiple providers

7. `io.write_json`:

   - `output/responses/query_2025-08-23T16-45-11.json` (full payload)
   - `output/debug/trace_...json` (plan, queries, timings)

8. response returned (truncated preview + path to file)

---

# hybrid query planner (detail)

## rule-based first (fast path)

- **intent detection (keywords):**

  - “top|best|highest rated” → `sort: rating DESC`
  - “less important|worst|low rated” → `sort: rating ASC`
  - “under X weeks|months|hours” → `durationDays <= …`
  - “from Coursera|FutureLearn|...” → platform scope
  - “top N” → `limit=N` (default 10)

- **entity extraction:**

  - topic: phrase after “in|on|about|for” or quoted `"..."`, else longest noun phrase

- **field routing per provider:**

  - search fields priority: `title > skills > whatYouLearn > shortIntro > topics > category/subCategory`

## gemini fallback (slow path, complex asks)

trigger if:

- no topic extracted, or
- asks like “courses to break into AI quickly with TensorFlow focus and low cost” (multi-criteria), or
- provider lacks fields needed by rule-based

**prompt ingredients:**

- allowed db/collection names
- per-collection field lists (only curated fields)
- allowed operators (no `$where`, no server-side JS)
- examples: NL → Mongo aggregation JSON
- your query

**gemini output (validated before run):**

- array of `{ db, collection, pipeline }`
- validate: **fields & ops whitelist**, strip disallowed ops, cap `$limit`, inject `$project` to canonical fields only

---

# ETL plan (raw → curated → courses)

## parse helpers

- `ratingparse.py`: `"4.9stars"` → `4.9` else `null`
- `timeparse.py`:

  - “3 months” → 90
  - “4 weeks” → 28
  - “Approximately 3 months to complete” → 90
  - if “Estimated timeApprox. 4 Months” → 120 (assume 30 days per month)

- `skills`: split on `,`, trim, drop empties, unique
- `topics`: split on `/` or `,`, trim
- `subtitleLanguages`: strip `Subtitles: `, split

## atlas search index (per `*_curated`)

example spec (conceptual):

```json
{
  "mappings": {
    "dynamic": false,
    "fields": {
      "title": { "type": "string", "analyzer": "lucene.standard" },
      "skills": { "type": "string" },
      "shortIntro": { "type": "string" },
      "whatYouLearn": { "type": "string" },
      "topics": { "type": "string" },
      "category": { "type": "string" },
      "subCategory": { "type": "string" },
      "searchIndex": { "type": "string" }
    }
  }
}
```

---

# API design (flask)

- `POST /query`

  - req: `{ "query": "string", "maxResults": 30, "providers": ["Coursera"], "explain": true }` (all optional except `query`)
  - resp:

    ```json
    {
      "query": "...",
      "tookMs": 143,
      "sourcesHit": ["Coursera"],
      "results": [ { canonical item ... } ],
      "outputFile": "output/responses/query_2025-08-23T16-45-11.json",
      "debugFile": "output/debug/trace_2025-08-23T16-45-11.json"
    }
    ```

- `GET /health` → `{ "ok": true }`
- `GET /last` → previews last JSON

**security:**
store `MONGO_URI`, `GEMINI_API_KEY` in `.env`; never log full keys; rate-limit `/query`.

---

# ranking & dedup (global)

- **dedup key:** `url` primary; fallback: lowercased `platform:title`
- **primary sort order:**

  1. if explicit intent “top/worst”: by `rating` with nulls last/first
  2. else relevance score:

     - `score = 3*hits(title) + 2*hits(skills) + 1*hits(desc)`
       (hits = keyword occurrences; also use Atlas Search `score` if available)

- secondary tiebreakers: `numViewers desc`, `durationDays asc`

---

# logging, observability, artifacts

- write one **debug trace** per query:

  - parse result (intent, topic, platform, limit)
  - per-source planned pipelines
  - actual pipelines run (post-validation)
  - row counts, timings
  - any LLM prompts/outputs (redact keys)

- application logs to `output/logs/app.log`
- add a **dry-run** flag to emit plan only without executing

---

# testing strategy

- **unit tests**: parsers (intent/topic), duration/rating parsers, adapters
- **integration tests**: sample data → query → expected constraints
- **golden files**: freeze query outputs for regression checks

---

# milestones (practical)

**M0 – bootstrap (1 day)**

- repo scaffold, `.env`, dependencies
- `init_db.py` connects to Atlas, creates DBs/collections, basic indexes

**M1 – ETL minimal (1–2 days)**

- load 10–30 sample rows per provider into `*_raw`
- curate → `*_curated` (rating/duration/skills/searchIndex)
- basic text/field indexes (and Atlas Search if ready)

**M2 – rule-based engine (1–2 days)**

- parser (intent/topic/platform/limit/sort)
- plan builder → Mongo pipelines (regex `$or` first)
- executor (parallel), adapters, merge/rank/dedup
- write JSON; add `/query` endpoint

**M3 – atlas search integration (0.5–1 day)**

- swap regex filter with `$search` when available
- use search scores where useful

**M4 – gemini fallback (1–2 days)**

- safe prompt + whitelist validator → build pipelines
- confidence heuristics for when to call gemini
- caching of NL → pipeline for repeated queries

**M5 – polish (0.5–1 day)**

- pagination, max limit caps, better snippets
- `/last`, `/health`, rate limiting

**M6 – docs & examples**

- README with quickstart, env setup, sample curls, example outputs

---

# “done” definition (for the baseline)

- ✅ `POST /query` handles queries like:

  - “top 5 data science courses from coursera”
  - “less important deep learning courses” (across all)
  - “python courses under 4 weeks”

- ✅ writes a timestamped unified JSON
- ✅ has debug plan & execution trace
- ✅ resilient: missing fields tolerated, null-safe sorting, sensible defaults

---

# nice-to-have (later)

- vector semantic search (Atlas Vector Search or external)
- per-user preferences (language, budget) & re-ranking
- learning-to-rank with feedback
- dedup across providers by content similarity (title fuzziness + Jaccard on skills)
- webhook to push results elsewhere
- cache layer (redis) for hot queries

---

if you’re good with this roadmap, say the word and i’ll drop:

1. the **Mongo DB/collection + index creation script**,
2. the **ETL normalize functions** (rating/duration/skills), and
3. a **minimal Flask server** with `/query` using the rule-based fast path.
