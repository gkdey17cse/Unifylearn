# Project Name : Automated Skill Extraction and Course Alignment

## Final Path We’ll Follow

#### A. Data Sources (meet “2 relational + 1 unstructured”)

1. **Relational ##1 – Oracle (Jobs A)**

   - Table: `Job(JID, JNAME, JDESCRIPTION, SALARY, PLACE)`
   - Notes: skills live _inside_ `JDESCRIPTION` (unstructured text).
   - Relational DB1 (Postgres on Neon.tech) → store structured tables like courses, job listings
   - Relational DB2 (PlanetScale / MySQL) → store structured schema like user profiles, career paths

2. **Relational ##2 – PostgreSQL (Courses)**

   - Tables (two different schemas to show integration):
   - Unstructured DB (MongoDB Atlas) → store raw scraped resumes, descriptions, and skill text

  - `uni_courses(course_id, institute, title, syllabus, credits, mode, city)`
  - `mooc_courses(id, provider, title, description, duration_weeks, cost, mode)`
  - Different schemas → we’ll federate into one logical view.

3. **Unstructured Source – MongoDB (Jobs B, raw docs)**

   - Collection: `JOBS`
   - Example doc:

     ```json
     {
       "ID": "J101",
       "Name": "ML Ops Engineer",
       "City": "Delhi",
       "Skills": ["Docker", "Kubernetes", "AWS", "CI/CD"],
       "Sal": "12 LPA",
       "Desc": "Own CI/CD pipelines, deploy models on AWS with Docker & K8s"
     }
     ```

   - We’ll also stash **scraped pages / PDFs** here as raw text blobs.

> This satisfies: **2 relational (Oracle + Postgres)** + **1 unstructured (Mongo)** + we’ll use an **open-source LLM** in multiple places.

---

#### B. Global (Unified) Schemas

We expose one **mediated/global schema** to the rest of the system:

- `IntegratedJob(job_id, title, city, salary, skills[])`
- `IntegratedCourse(course_id, provider_type{'UNI','MOOC'}, name, skills[], duration, mode, cost, institute_or_provider)`

###### Schema Mapping (declarative config in code)

```python
SCHEMA_MAP = {
  "oracle.jobs": {
    "id": "JID", "title": "JNAME", "city": "PLACE",
    "salary": "SALARY", "desc": "JDESCRIPTION", "skills_source": "desc"
  },
  "mongo.jobs": {
    "id": "ID", "title": "Name", "city": "City",
    "salary": "Sal", "desc": "Desc", "skills_source": "Skills"
  },
  "pg.uni_courses": {
    "id": "course_id", "name":"title", "skills_src":"syllabus",
    "provider_type":"UNI", "duration":"credits", "mode":"mode",
    "provider_or_inst":"institute", "cost": None
  },
  "pg.mooc_courses": {
    "id": "id", "name":"title", "skills_src":"description",
    "provider_type":"MOOC", "duration":"duration_weeks", "mode":"mode",
    "provider_or_inst":"provider", "cost":"cost"
  }
}
```

This keeps the “integration” logic explicit and defensible.

---

#### C. Where the Open-Source LLM Is Used

We’ll use **one small, open-source instruction model** (e.g., **Mistral-7B-Instruct** or **Llama-3-8B-Instruct** in **GGUF** format via `llama-cpp-python`) for:

1. **Query Parsing (NLU)**
   Convert user text → `{role, location, duration, price_range, mode}`.
2. **Role Expansion**
   “MLOps” → {“ML Engineer”, “AI Engineer”, “DevOps”, “Data Engineer”} (top-k).
3. **Skill Extraction from Unstructured JDs**
   From `JDESCRIPTION` (Oracle) and `Desc` (Mongo) → canonical skills list.
4. **(Optional) Natural-language summary**
   Short rationale: “Why these courses, which skills they cover.”

> Everywhere else we’ll prefer deterministic code (regex/rules/embeddings) to keep it robust and explainable.

---

#### D. End-to-End Execution Flow (Baseline)

1. **Simple Form (Frontend) → POST `/recommend`**
   Payload: `{ query_text: "...", filters?: {...} }`

2. **Pre-clean**
   Lowercase, trim, normalize city names.

3. **LLM: Query Parsing + Role Expansion**

   - Extract `{role, location, constraints}`
   - Expand roles to improve recall.

4. **Planner**
   Create sub-queries:

   - Q1: Jobs from Oracle (by location + expanded roles)
   - Q2: Jobs from Mongo (same filters)
   - Q3: Courses from Postgres (uni + mooc)

5. **Relational ##1: Oracle Jobs**

   - SQL fetch: `JID, JNAME, JDESCRIPTION, SALARY, PLACE`

6. **Unstructured: Mongo Jobs**

   - Query docs; get `Name, City, Skills, Desc, Sal`

7. **LLM Skill Extraction (only when needed)**

   - For Oracle `JDESCRIPTION` and Mongo `Desc`
   - Prompt returns JSON array of skills.

8. **Merge & Normalize Skills**

   - Union structured + extracted skills
   - Normalize via a **skills map** (YAML/dict):
     `"k8s"→"Kubernetes", "gcp"→"Google Cloud", "nn"→"Neural Networks"`
   - Optional: embeddings (sentence-transformers `all-MiniLM-L6-v2`) to catch fuzzy cases.

9. **Skill Weighting**

   - Frequency/TF-IDF across all matching jobs (location-filtered)
   - Output: `[(skill, weight), ...]` (demand profile)

10. **Relational ##2: PostgreSQL Courses (two schemas)**

    - Fetch from `uni_courses` and `mooc_courses`.

11. **Federation (Mediation Layer)**

    - Apply `SCHEMA_MAP` to build a **single logical view** `IntegratedCourse[...]`.

12. **Course Skill Extraction**

    - Rules/dictionary first; LLM fallback for fuzzy syllabus text.
    - Produce `skills[]` per course.

13. **Matching & Coverage**

    - Score each course vs **demanded skills**:
      `coverage(course) = Σ weight(skill) for skills taught by course`

14. **Return Results**

    - JSON to frontend:

      - Top demanded skills (with weights)
      - Ranked courses (uni + mooc), fields: name, provider/institute, duration, mode, cost, coverage

    - (Optional) LLM one-paragraph rationale.

> **Baseline ends here** (Step 16 in your plan).
> (Optional Innovation) Resume parsing + skill gap can be added later.

---

#### E. Tech Stack (Minimal, Stable, Open)

**Language:** Python 3.11

**Backend:**

- **FastAPI** (API)
- **uvicorn** (server)
- **pydantic** (validation)

**Relational DBs:**

- **Oracle** (Jobs A) → `cx_Oracle` (or `oracledb`) + SQLAlchemy
- **PostgreSQL** (Courses) → `psycopg2-binary` + SQLAlchemy

**Unstructured DB:**

- **MongoDB Atlas (free tier)** → `pymongo`

**NLP / LLM:**

- **llama-cpp-python** (runs quantized open models locally)

  - Model: **Mistral-7B-Instruct** _or_ **Llama-3-8B-Instruct**, **Q4_K_M GGUF**

- **spaCy** (`en_core_web_sm`) for light NER/tokenization
- **sentence-transformers** (`all-MiniLM-L6-v2`) for embedding similarity (optional but useful)

**ETL / Federation / Utils:**

- **pandas** (CSV/JSON handling)
- **SQLAlchemy** (ORM & connections)
- **APScheduler** (optional: periodic sync jobs)
- **PyYAML** (skills synonym map)

**Frontend (very simple):**

- HTML + Tailwind CDN + a tiny JS fetch()
- FastAPI’s Jinja2 templates (optional) for server-side rendering

**Dev/Infra:**

- Git/GitHub
- Docker (optional)
- Deployment: Render/Railway (optional)
- Logging: `loguru` (optional)

---

#### F. Concrete Prompts (so we’re repeatable)

**1) Query Parsing prompt (LLM)**

```
You are a parser. Extract a JSON with keys: role, location, duration_months (int or null), price_max (int or null), mode (online/offline/hybrid/any).
Text: "<<USER_QUERY>>"
Return ONLY JSON.
```

**2) Role Expansion prompt**

```
Given a target role "<<ROLE>>", list 5 closely related roles users might mean in job search.
Return a JSON array of distinct role strings.
```

**3) Skill Extraction from JD**

```
Extract technical skills/tools/frameworks from the following job text.
Return a JSON array of canonical skill names only.
Text: "<<JD_TEXT>>"
```

(We’ll post-process to lowercase + map via synonyms.)

---

#### G. Implementation Roadmap (week-by-week)

**Week 1 – Project Skeleton**

- FastAPI app, `/recommend` endpoint
- Connectors: Oracle, Postgres, Mongo (env-driven URIs)
- Seed small sample data (CSV → Postgres, JSON → Mongo)

**Week 2 – LLM & Parsing**

- Integrate `llama-cpp-python` with chosen model
- Implement query parsing + role expansion
- Build the sub-query planner (no UI yet)

**Week 3 – Jobs Integration**

- Oracle fetch + LLM skill extraction from `JDESCRIPTION`
- Mongo fetch + skills union + normalization + weighting

**Week 4 – Courses Integration & Federation**

- Fetch from `uni_courses` + `mooc_courses`
- Apply `SCHEMA_MAP` → `IntegratedCourse` view
- Course skill extraction (rules + LLM fallback)

**Week 5 – Matching & Output**

- Coverage scoring + ranking
- Return JSON + simple HTML page (cards + filters)

**Week 6 – Polish & Paper Hooks**

- Logging of sub-steps (for Task-2 decomposition evidence)
- Add small evaluation set; compute latency & P\@K
- (Optional) Resume parsing + skill-gap index

---

#### H. What You’ll Show in Demo / Report

- **Task-1:** Two relational (Oracle + Postgres) + one open-source LLM + unstructured (Mongo/JD text).
- **Task-2:** Explicit query decomposition + federation (code & logs).
- **Task-3 (optional):** Resume-based skill gap + SGI metric.
- **UI:** Simple form → results table/cards + “top demanded skills” list.
- **Innovation (even without resume):** Heterogeneous schema mediation + LLM-aided extraction + coverage scoring.

---

If this looks good, I can draft:

- the **DB DDLs** (Oracle & Postgres),
- the **global schema classes**,
- and a **FastAPI route skeleton** with the exact I/O contracts.
