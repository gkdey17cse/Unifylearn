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
│   │   │   ├── llm_interface.py # NEW: LLM-based query generation
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── config.py          # Configs (API keys, DB URLs)
│   │   │   └── text_utils.py      # Text preprocessing helpers
│   ├── io_utils/
│   │   ├── __init__.py
│   │   └── write_json.py          # Exporting query results
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
      main.py                # FastAPI app initialization & routes mounting
      routes/
        __init__.py
        query_routes.py      # Handles incoming requests, calls Gemini for query generation
      services/
        __init__.py
        db_service.py        # Handles database queries
        federation_service.py # Executes federated queries
        plan_builder.py      # Builds the federated execution plan
        adapters.py          # Adapter layer between federation & DB
      nlp/
        __init__.py
        parser_rule_based.py # Existing rule-based parser (kept as fallback or hybrid)
        llm_interface.py     # NEW: Handles communication with Google Gemini API
      utils/
        __init__.py
        config.py            # Loads configs, including Gemini API key
        text_utils.py
    io_utils/
      __init__.py
      write_json.py
  results/                   # Stores query results (JSON/CSV/etc.)
  scripts/
    run_query.py             # CLI script to trigger a query
  .env                       # Contains GEMINI_API_KEY and other secrets
  requirements.txt           # Add `google-generativeai` here
  README.md
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

Perfect! Now that we are aligned on the **exact project structure** and have integrated the `llm_interface.py`, let’s walk through:

---

## **How to Run the Backend**

### **1. Set up your environment**

* Make sure you have your virtual environment active (`IIAProject`).
* Install dependencies:

```bash
pip install -r requirements.txt
```

* Set your `.env` file with:

```bash
GEMINI_API_KEY="your_google_gemini_api_key"
MONGO_URI="your_mongodb_connection_uri"
```

---

### **2. Start the FastAPI Server**

Your `main.py` (FastAPI app entry point) should already have something like:

```bash
uvicorn src.app.main:app --reload
```

---

## **Flow After User Submits a Query**

### **Step-by-Step Data Flow**

1. **User Sends Query (Frontend → Backend)**

   * Endpoint: `POST /query`
   * Body:

     ```json
     {
       "query": "Show me top 5 courses in Data Science from Coursera"
     }
     ```

2. **Query Routing (`query_routes.py`)**

   * Extracts the query string.
   * Calls the **rule-based parser** (`parser_rule_based.py`) → produces a rough structure (keywords, filters).
   * Sends the same user query to **Google Gemini (`llm_interface.py`)** for deeper semantic analysis.

3. **LLM Query Generation (`llm_interface.py`)**

   * Gemini returns a structured interpretation (intent, databases to use, filters).
   * This is returned as `llm_context`.

4. **Federation Layer (`federation_service.py`)**

   * Combines **rule-based parse + LLM context**.
   * Decides which database(s) to query (from 4 sources).
   * Calls the database adapters (`db_service.py` + `adapters.py`) for each relevant DB.

5. **Data Retrieval (`db_service.py`)**

   * Each adapter connects to its respective DB (MongoDB collections in your case).
   * Executes queries (currently basic; later, we will let Gemini refine them to DB-specific queries).

6. **Federation Aggregation**

   * Combines the results from all databases.
   * Applies any ranking or post-processing (optional LLM re-ranking in the future).

7. **Response Formation**

   * Saves raw results as JSON in `/results/`.
   * Returns a summary response with:

     * Original query
     * Parsed query
     * LLM context
     * Results preview (top 10)
     * Path to full results JSON

---

## **How Data Will Be Fetched & Combined**

* **LLM determines** which DBs are relevant.
* The federation service builds a **query execution plan** (simple: call each relevant collection with a filter).
* Each DB adapter fetches its results.
* Results are **merged in-memory (Python)**.
* Optional: **Ranking or sorting using LLM (later stage)**.
* Final merged result is sent to the user.

---

## **Example Workflow**

### User sends:

```json
{ "query": "Show top 5 free Python courses from Coursera and edX" }
```

* Rule-based: Extracts `{"keywords": ["Python", "courses"], "platforms": ["Coursera","edX"], "limit":5}`
* LLM: Enhances → identifies which databases to hit: `Coursera_DB`, `edX_DB`.
* Federation service queries both.
* Merges results: Top 5 free Python courses.

Returns:

```json
{
  "query": "Show top 5 free Python courses from Coursera and edX",
  "results_count": 5,
  "results_preview": [...],
  "out_file": "./results/query_20250824T163000Z.json",
  "took_seconds": 1.2
}
```

---

## **What’s Next?**

1. Add **MongoDB adapters** for each of the 4 databases.
2. Make **federation\_service** actually dispatch queries based on Gemini output.
3. Add **ranking/scoring (optional)** for better presentation.

---

Would you like me to now:

1. **Write the federation\_service.py** so it uses both rule-based + LLM output to hit all 4 MongoDB collections?
2. Or first create **MongoDB adapters for each database** (the minimal working version)?
3. Or both in one go so you can immediately fetch real data?

Which path do you want next?
