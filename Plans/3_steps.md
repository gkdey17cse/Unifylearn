# Planning Absolute

1. **Capture user input** — Take a messy natural-language query (and optional resume upload) from the UI.
2. **Pre-clean the text** — Normalize casing, strip emojis/URLs, and standardize location names.
3. **Entity extraction (LLM/NER)** — Pull out role/title, location, seniority, and constraints (budget, mode, timeline).
4. **Job-title expansion (LLM)** — Generate related/nearby roles (e.g., “MLOps” ⇒ {“ML Engineer”, “DevOps”, “DL Engineer”, “AI Engineer”}) and keep top-K.
5. **Sub-query planner** — Decompose into atomic tasks: fetch jobs, extract skills, fetch courses, match, compute gaps, rank, render.
6. **Structured job search** — Query the relational Jobs DB for postings matching {expanded roles × location}.
7. **Unstructured JD skill extraction (LLM)** — For each job description text, extract a canonical list of skills/tech/tools.
8. **Structured skills merge** — Union skills from (a) structured columns and (b) LLM-extracted skills, deduped.
9. **Skill normalization** — Map synonyms to canonical labels (e.g., “GCP” → “Google Cloud”, “NN” → “Neural Networks”).
10. **Skill weighting** — Compute importance scores (e.g., TF-IDF/frequency across postings) to prioritize in-demand skills.
11. **Fetch university courses (relational)** — Query the IIT/NIT/IIIT (simulated) courses DB for titles, descriptions, outcomes, prerequisites.
12. **Fetch online courses (relational)** — Query MOOCs DB (Coursera/edX/NPTEL dataset) with provider, syllabus, duration, cost, mode.
13. **Schema harmonization (federation layer)** — Normalize both course sources into a common schema: {course, provider, skills, level, duration, mode}.
14. **Course skill extraction** — From course descriptions/syllabi, extract/normalize skills (rules + LLM for fuzzy terms).
15. **Skill–course matching** — Match required job skills to courses via exact keywords + embedding similarity (top matches per skill).
16. **Coverage scoring** — Score each course by how many high-weight skills it covers (and how well).
17. **Resume parsing (innovation)** — If resume provided, extract existing skills/courses/certs to personalize results.
18. **Skill-gap computation (innovation)** — Compute Missing = RequiredSkills − ResumeSkills, and focus recommendations on gaps.
19. **Path recommendation** — Build a minimal set of courses that covers the gap (set-cover style heuristic; sequence by prerequisites).
20. **Result ranking** — Rank by (coverage × importance) − redundancy, with tie-breakers (level, duration, cost, provider).
21. **Explainability (LLM)** — Generate a short rationale: why these courses, which skills they close, and suggested order.
22. **UI rendering** — Show cards/tables: top skills, missing skills, recommended university courses, recommended MOOCs, and a learning roadmap.
23. **Filters & controls** — Let user filter by provider, cost, duration, mode (online/offline), and re-rank on the fly.
24. **Feedback loop** — Capture clicks/saves to improve ranking weights and store anonymous analytics for evaluation.
25. **Caching & reuse** — Cache frequent role/location queries and precomputed skill maps for snappy responses.
26. **Evaluation harness** — Keep a small gold set of queries and measure precision\@K for skills/courses and latency.
27. **Reporting hooks** — Log sub-query outputs for your paper: decomposition, federation joins, coverage scores, SGI metric.
28. **Skill Gap Index (metric)** — Report SGI = |MissingSkills| / |RequiredSkills| before vs after recommendations.
29. **Safety & privacy** — Redact PII from resumes and store only derived skill vectors, not raw documents.
30. **Deliverables packaging** — Provide demo UI, API spec, dataset schema, ablations (w/ and w/o resume, w/ and w/o LLM), and poster figures.

# End to End Path
Totally—your baseline ends at **Step 16 (Coverage scoring)**, and **Steps 17–18 (resume parsing + skill-gap)** are your innovation add-ons. You’ve got it right ✅

Here’s a clear, example-driven walkthrough of the **entire project idea → what each step does → what you’ll build → what the outputs look like**.

---

# End-to-end flow (with a concrete example)

### User query (example)

> “I want to make a career in **MLOps** in **Kolkata**.”

We’ll assume **no resume** for the baseline; we’ll mention where resume fits for innovation.

---

## 1) Capture user input

* **Do:** Take free-text query from UI (plus optional resume upload).
* **Output:** Raw string (and optional file).

## 2) Pre-clean the text

* **Do:** Lowercase, strip URLs/emojis, normalize city (“Calcutta”→“Kolkata”), trim spaces.
* **Output:** Clean string.

## 3) Entity extraction (LLM/NER)

* **Do:** Extract `{role: "MLOps", location: "Kolkata"}` and optional constraints (mode, cost).
* **Output:** `{"role": "MLOps", "location": "Kolkata"}`

## 4) Job-title expansion (LLM)

* **Do:** Expand near roles to improve recall:
  `["MLOps Engineer", "ML Engineer", "AI Engineer", "Data Engineer", "DevOps Engineer"]` (keep top-K).
* **Output:** Expanded roles list.

## 5) Sub-query planner

* **Do:** Create atomic tasks: fetch jobs → extract skills → fetch courses → extract course skills → match → score.
* **Output:** Executable plan (list of steps with inputs/outputs).

## 6) Structured job search (relational)

* **Do:** SQL on Jobs DB:

  ```
  SELECT job_id, title, city, skills_structured, description
  FROM jobs
  WHERE city='Kolkata' AND title ILIKE ANY (ARRAY['%MLOps%','%ML Engineer%','%DevOps%','%AI Engineer%','%Data Engineer%']);
  ```
* **Output:** Rows of postings (some have `skills_structured`, all have `description`).

## 7) Unstructured JD skill extraction (LLM)

* **Do:** For each `description`, prompt the LLM to extract skills as JSON.

  * Prompt (short):
    “Extract technical skills/tools/frameworks from this job description. Return a JSON array of canonical skill names only. JD: <text>”
* **Output (example per JD):**
  `["Python","Docker","Kubernetes","AWS","CI/CD","TensorFlow","MLflow","Linux"]`

## 8) Structured skills merge

* **Do:** Union of `skills_structured` and LLM-extracted skills; dedupe.
* **Output (across all JDs):** A multiset of skills.

## 9) Skill normalization

* **Do:** Map synonyms to canonical labels (rulebook + small LLM check):

  * “GCP”→“Google Cloud”, “K8s”→“Kubernetes”, “NN”→“Neural Networks”.
* **Output:** Clean canonical skill list per JD.

## 10) Skill weighting

* **Do:** Compute importance by frequency/TF-IDF across postings.
  **Example (top 10 with weights):**

  * Python 0.72, Docker 0.66, Kubernetes 0.61, AWS 0.55, CI/CD 0.49, Linux 0.46, TensorFlow 0.40, MLflow 0.33, SQL 0.30, PyTorch 0.28

## 11) Fetch university courses (relational)

* **Do:** SQL on **University Courses DB** (simulated IIT/NIT/IIIT table):

  ```
  SELECT course_id, institution, title, description, level, duration, mode
  FROM uni_courses
  WHERE department ILIKE '%CSE%' OR title ILIKE ANY (ARRAY['%cloud%','%ml%','%devops%','%data%']);
  ```
* **Output:** Course rows with descriptions/syllabi.

## 12) Fetch online courses (relational)

* **Do:** SQL on **MOOCs DB** (Coursera/edX/NPTEL-like dataset):

  ```
  SELECT course_id, provider, title, description, duration_weeks, cost, mode
  FROM mooc_courses
  WHERE title ILIKE ANY (ARRAY['%mlops%','%devops%','%cloud%','%ml%'])
     OR description ILIKE ANY (ARRAY['%docker%','%kubernetes%','%mlflow%','%ci/cd%']);
  ```
* **Output:** MOOC rows.

## 13) Schema harmonization (federation layer)

* **Do:** Map both sources to a common schema:
  `{course_id, provider, institution, title, skills[], level, duration, mode, cost}`
* **Output:** Unified course table (logical view).

## 14) Course skill extraction

* **Do:** Extract skills from each course description/syllabus:

  * First: dictionary/rules (fast).
  * Then (fallback/fuzzy): LLM/embeddings to catch “hands-on CI pipelines” → “CI/CD”.
* **Output:** `skills[]` per course (canonical labels).

## 15) Skill–course matching

* **Do:** Score each course against **required skills** with a mix of:

  * Exact overlap count (canonical set match), and
  * Embedding similarity (course text vs skill names).
* **Output:** Per-course `match_vector` and `match_score`.

## 16) Coverage scoring (final baseline output)

* **Do:** Weight overlaps by **skill importance** from Step 10.
  **Example formula:**
  `coverage(course) = Σ_{skill in course∩required} weight(skill)`
* **Output:** Ranked list of recommended courses (baseline **final output**).

---

# What the outputs look like (sample)

### A) Top required skills (from Kolkata MLOps jobs)

```
[
  {"skill":"Python","weight":0.72},
  {"skill":"Docker","weight":0.66},
  {"skill":"Kubernetes","weight":0.61},
  {"skill":"AWS","weight":0.55},
  {"skill":"CI/CD","weight":0.49},
  {"skill":"Linux","weight":0.46},
  {"skill":"TensorFlow","weight":0.40},
  {"skill":"MLflow","weight":0.33}
]
```

### B) Example courses after federation (SIMULATED names/fields)

```
[
  {
    "title":"Modern MLOps: From Model to Production",
    "provider":"NPTEL (simulated)",
    "skills":["MLOps","MLflow","Docker","CI/CD"],
    "duration_weeks":8,
    "mode":"online",
    "coverage":0.66  // (weights for Docker 0.66 + CI/CD 0.49 + MLflow 0.33)
  },
  {
    "title":"Cloud & Containers",
    "provider":"IIIT (simulated)",
    "skills":["AWS","Docker","Kubernetes"],
    "duration_weeks":10,
    "mode":"offline",
    "coverage":1.82 // AWS 0.55 + Docker 0.66 + Kubernetes 0.61
  },
  {
    "title":"Deep Learning Systems",
    "provider":"IIT (simulated)",
    "skills":["TensorFlow","Python","Linux"],
    "duration_weeks":12,
    "mode":"offline",
    "coverage":1.58 // 0.40 + 0.72 + 0.46
  },
  {
    "title":"DevOps Foundations",
    "provider":"Coursera-like (simulated)",
    "skills":["CI/CD","Docker","Kubernetes","Linux"],
    "duration_weeks":6,
    "mode":"online",
    "coverage":2.22 // 0.49 + 0.66 + 0.61 + 0.46
  }
]
```

### C) Final UI (baseline)

* **Panel 1:** “In-demand skills for MLOps in Kolkata” (bar chart with weights).
* **Panel 2:** “Recommended courses” (cards sorted by `coverage`).
* **Panel 3 (optional text):** LLM-generated 3–4 line rationale.

> *“To target MLOps roles in Kolkata, strengthen Docker, Kubernetes, AWS, and CI/CD. We recommend ‘Cloud & Containers’ and ‘DevOps Foundations’ for highest coverage of employer-demanded skills.”*

---

# Innovation add-ons (where resume fits)

## 17) Resume parsing (innovation)

* **Do:** Parse PDF/DOCX to extract `resume_skills` and prior courses/certs (LLM + rules).
* **Use:** Personalize recommendations.

## 18) Skill-gap computation (innovation)

* **Do:** `missing_skills = required_skills − resume_skills`.
* **Effect:** Re-rank to highlight courses covering **missing** skills first.
* **Extra metric:** Show **Skill Gap Index = |missing| / |required|**.

---

# What you have to build (step-by-step implementation path)

### Phase A — Data & Schemas

1. **Design DB schemas**

   * `jobs(job_id, title, city, skills_structured[], description TEXT)`
   * `uni_courses(course_id, institution, title, description, level, duration, mode)`
   * `mooc_courses(course_id, provider, title, description, duration_weeks, cost, mode)`
2. **Seed small datasets**

   * 200–500 job rows (can be curated/simulated).
   * 100–200 courses split across uni & MOOCs.

### Phase B — Services & APIs

3. **Backend (FastAPI)**

   * `/parse_query` → entities
   * `/jobs` → postings for roles×city
   * `/skills/extract` → LLM extraction for JDs
   * `/courses/search` → federated course view
   * `/match/recommend` → ranked course list

### Phase C — NLP/LLM logic

4. **Entity extraction**

   * spaCy NER + rules; or small instruct LLM.
5. **Job-title expansion**

   * Static map + LLM backoff; keep top-K unique.
6. **JD skill extraction**

   * Skill dictionary (regex) → LLM fallback.
7. **Normalization**

   * YAML synonym map (editable): `{"k8s":"Kubernetes","gcp":"Google Cloud"}`

### Phase D — Scoring & Matching

8. **Skill weighting**

   * Frequency or TF-IDF across the selected postings.
9. **Course skill extraction**

   * Same dictionary + LLM fallback on syllabus text.
10. **Coverage scoring**

    * Implement the formula and rank.

### Phase E — UI

11. **Frontend (Streamlit or React)**

    * Input box, city dropdown.
    * Charts for skill weights; cards for courses.
    * Filters: mode (online/offline), duration, provider.

### Phase F — (Optional) Innovation

12. **Resume parsing**

    * PDF text → skill extraction → `resume_skills`.
13. **Gap-aware ranking**

    * Prioritize courses covering `missing_skills`.

### Phase G — Evaluation & Paper Artifacts

14. **Ablations**

    * With vs without LLM extraction.
    * With vs without title expansion.
15. **Metrics**

    * Top-N skill precision (manual gold set).
    * Latency & throughput.
    * Skill Gap Index before/after (if resume used).
16. **Figures**

    * Pipeline diagram, federation view, coverage chart.

---

# Minimal tech stack (fits your machine)

Got it 👍 you’re thinking in the right direction. Since you’ve decided to **stick with Python for everything** (except a little JS in frontend if needed), I’ll give you a **complete, honest tech stack** with reasoning for each choice. I’ll cover **language, framework, libraries, database, infra, and integration tools**.

---

## 🛠️ **Tech Stack Breakdown**

### 1. **Frontend**

* **Language**: HTML + CSS + JS
* **Framework / Libraries**:

  * **TailwindCSS (via CDN)** → for quick and beautiful UI.
  * **Vanilla JS** → for DOM interactivity (checkbox filters, etc).
  * **EJS (Embedded JS Templates)** or **Jinja2** (if rendering via FastAPI templates).
  * **Bot UI**:

    * A **chat widget** (JS-based, minimal, e.g., [BotUI](https://docs.botui.org/) or a custom floating div styled with Tailwind).
* **Reasoning**: Since UI is not the main focus, keep it **lightweight, clean, and simple**.

---

### 2. **Backend**

* **Language**: Python
* **Framework**:

  * **FastAPI** → modern, async-friendly, perfect for building APIs quickly.
* **Key Libraries**:

  * **uvicorn** → ASGI server for FastAPI.
  * **pydantic** → data validation for API requests.
  * **SQLAlchemy** → ORM for PostgreSQL/MSSQL.
  * **motor** (async Mongo driver) if using MongoDB.
  * **pandas** → for CSV/JSON integration.
  * **requests/httpx** → to fetch external APIs (job/course APIs).

---

### 3. **Databases**

You suggested **two types** → I think that’s actually a **good idea** (shows federation + syncing).

* **PostgreSQL (or MSSQL)** → store structured data (job postings, course details, metadata).
* **MongoDB Atlas (free cluster)** → store semi-structured/unstructured data (scraped descriptions, NLP-processed content).

💡 Prof might check syncing → so we can implement a **basic ETL sync pipeline** that pushes a record into both DBs.

---

### 4. **ETL / Integration Layer**

Since professor suggested syncing, we’ll show that we thought about it seriously.

* **Option A (lightweight custom)**:

  * Use **Airflow** (heavier) or **Apache NiFi** (too much for small project).
  * OR simply **implement a Python ETL pipeline** with `pandas` + `sqlalchemy` + `pymongo`.
  * We can write a background scheduler with **Celery** or **APScheduler** to sync data every X minutes.
* **Recommendation**: For project demo → stick with **Python ETL (pandas/sqlalchemy/motor)**. (Airflow can be mentioned as future scope).

---

### 5. **NLP / AI Layer**

* **Libraries**:

  * **spaCy** → for NER (extract skills, job roles, locations).
  * **Transformers (HuggingFace)** → to use small pretrained LLM (for query understanding).
  * **Sentence Transformers** → for semantic search (user query → match job/course text).
  * **scikit-learn** → for classical ML (if required, e.g., intent classification).
* **Flow**:
  User Query → NLP Parsing → Extract Entities (job role, location, duration) → Query Database → Return Results.

---

### 6. **Infra & Dev Tools**

* **GitHub** → version control.
* **Docker (optional)** → containerize app if needed.
* **Render / Railway / Vercel (free-tier deploy)** → deploy backend + frontend.
* **MongoDB Atlas (free cluster)** → host MongoDB.
* **Neon.tech (free PostgreSQL)** or **Supabase** → for Postgres hosting.

---

## 🚀 **Basic Version (MVP Flow)**

1. **Frontend**: Floating chatbot UI + filter checkboxes.
2. **Backend (FastAPI)**: Receives query → calls NLP pipeline → queries Mongo/Postgres → formats response.
3. **ETL Sync**: Simple Python function that writes job/course details to both DBs (can be triggered manually or by scheduler).
4. **Frontend Display**: Returns a **card-style list** of jobs/courses with filters.

---

✅ This stack will:

* Use **Python everywhere** (so no major context switching).
* Show **ETL/data federation** (prof will like it).
* Keep frontend **lightweight but functional**.
* Allow **cloud database access** (Mongo Atlas + Neon PostgreSQL).

---

# Final Plan
Got it 👍 keeping it **simple & clean**.
Let’s lock down the **final project scope + architecture** in a way that you (and I) can always stay in sync for any future task.

---

## 🔹 Final Project Plan (Agreed Baseline)

### 1. **User Input**

* A **simple web form** (no chatbot UI).
* User types natural query:
  Example → *“Find me ML Ops courses in Delhi with duration < 6 months”*

---

### 2. **Processing Layer**

* **LLM step**:

  * Parse natural query → structured fields (Job Role, Location, Duration, Fees, Skills, etc.).
  * Expand job role if needed (e.g., ML Ops → ML, AI, DevOps).

---

### 3. **Databases**

* **Relational DB 1 → PostgreSQL**: main course database.
* **Relational DB 2 → MySQL**: secondary DB (to show replication/ETL syncing).
* **Unstructured DB → MongoDB (or ElasticSearch)**:

  * Stores raw scraped course descriptions / job ads / text data.
  * LLM extracts structured info → sync into PostgreSQL.

---

### 4. **ETL / Sync**

* A **Python ETL pipeline**:

  * Periodically sync data from unstructured source → structured DB.
  * Keep MySQL in sync with PostgreSQL (incremental updates).

---

### 5. **Query Execution**

* After parsing, the query is run on **Postgres/MySQL**.
* If needed, MongoDB text search is also triggered (for fuzzy matches).

---

### 6. **Final Output**

* Show results in a **summary table** (HTML page):

  * Course Name | Institute | Location | Duration | Fees | Mode
* Also show a **final summary sentence** generated by LLM:
  *“Found 3 ML Ops courses in Delhi under 6 months, starting from ₹25,000.”*

---

✅ This design ensures:

* **2 relational DBs covered (Postgres + MySQL)**
* **1 unstructured DB covered (Mongo/ElasticSearch)**
* **LLM used in 3 places (query parsing, role expansion, info extraction)**
* **Simple form UI** → no chatbot overhead
* **Final summary generated** for clarity

---