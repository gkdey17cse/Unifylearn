# Project Name : Automated Skill Extraction and Course Alignment

##  **Final Path We’ll Follow**

---

#### **A. Data Sources**

(Meets “2 relational + 1 unstructured” requirement)

**Relational ##1 – Oracle (Structured Jobs A)**

```sql
Job(JID, JNAME, JDESCRIPTION, SALARY, PLACE)
```

* Issue: `JDESCRIPTION` contains unstructured skills text → needs LLM parsing.

**Relational ##2 – PostgreSQL (Courses)**
Two heterogeneous schemas:

```sql
uni_courses(course_id, institute, title, syllabus, credits, mode, city)

mooc_courses(id, provider, title, description, duration_weeks, cost, mode)
```

* Both normalized into one logical **IntegratedCourse schema**.

**Unstructured – MongoDB Atlas (Jobs B, raw docs)**

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

* Also holds scraped pages, resumes, PDFs in raw text.

✅ This setup satisfies **2 relational + 1 unstructured** data source rule.

---

#### **B. Global Unified Schema**

We expose a mediated schema for federation:

```yaml
IntegratedJob:
  job_id
  title
  city
  salary
  skills[]     ## extracted from job desc
  subjects[]   ## skills → subjects (via LLM)

IntegratedCourse:
  course_id
  provider_type {UNI, MOOC}
  name
  skills[]     ## extracted from syllabus/description
  subjects[]   ## skills → subjects (via LLM)
  duration
  mode
  cost
  institute_or_provider
```

---

#### **C. LLM Intervention Points**

We’ll run an **instruction-tuned LLM (Mistral-7B-Instruct / LLaMA-3)** at these stages:

1. **Query Parsing**

   * User query → structured `{role, location, duration, cost, mode}`

2. **Skill Extraction**

   * From Oracle `Job.JDESCRIPTION` & Mongo `Desc`.
   * Deduplicate skills, normalize synonyms.

3. **Skill → Subject Mapping (Innovation)**

   * Example:

     * `[TensorFlow, CNN, PyTorch] → Deep Learning`
     * `[Docker, Kubernetes, CI/CD] → MLOps`

4. **Frontend Humanization**

   * Show skills as human-readable lists:

     * *“For this role, you’ll need Deep Learning, MLOps, SQL, and Cloud Skills.”*

5. **Course Generation**

   * Given skill set, generate course suggestions (text-level names + descriptions).
   * Example:

     * Skills: Deep Learning → “Intro to Deep Learning”, “Neural Networks Advanced”.

6. **Optional Justifications**

   * LLM generates rationale:

     * *“This course matches because it covers CNNs & RNNs, which are essential for Deep Learning roles.”*

---

#### **D. Execution Flow**

1. **User Query → `/recommend`**

2. **LLM: Parse Query + Expand Roles**

   * “AI Engineer” → {ML Engineer, Data Scientist, MLOps Engineer}

3. **Fetch Jobs**

   * From Oracle SQL (`Job` table)
   * From MongoDB (raw docs)

4. **LLM: Skill Extraction + Normalization**

   * Unified, deduped skill list generated.
   * Printed / stored in JSON array → shown in frontend.

   Example shown to user:

   ```json
   {
     "job_role": "MLOps Engineer",
     "required_skills": ["Docker", "Kubernetes", "AWS", "CI/CD", "Deep Learning"]
   }
   ```

5. **LLM: Skill → Course List**

   * For each skill set, LLM proposes **course names/descriptions**.
   * Results kept in backend array (not persisted).

6. **Federated Query Execution**

   * Use generated course names to query:

     * `uni_courses` (Postgres)
     * `mooc_courses` (Postgres)
   * Apply semantic similarity (embeddings) to handle mismatches.
   * E.g. “Intro to Deep Learning” \~ “Deep Neural Networks”.

7. **Result Ranking & Return**

   * Courses scored by overlap with skill set & user constraints (cost, duration, mode).
   * Final response returned in JSON → rendered in frontend “Cart View”.

   Example response:

   ```json
   {
     "skills_extracted": ["Docker", "Kubernetes", "Deep Learning"],
     "courses_recommended": [
       {
         "provider": "IIT Madras",
         "name": "Deep Neural Networks",
         "type": "UNI",
         "duration": "12 weeks",
         "cost": "Free"
       },
       {
         "provider": "Coursera",
         "name": "Intro to Deep Learning",
         "type": "MOOC",
         "duration": "8 weeks",
         "cost": "$49"
       }
     ]
   }
   ```

---

#### **E. Tech Stack**

* **API Layer:** FastAPI (Python 3.11)
* **Databases:**

  * Oracle → Structured Jobs A
  * PostgreSQL → Uni + MOOC courses
  * MongoDB Atlas → Raw Jobs B (Unstructured)
* **LLM Processing:** Llama/Mistral (via llama.cpp / vLLM)
* **Semantic Search:** FAISS / SentenceTransformers embeddings
* **Frontend:** React (Cart View)

---

⚡ This final path ensures:

* **Meets professor’s “2 relational + 1 unstructured” requirement**
* **LLM = innovation** (skills → subjects → courses)
* **Data shown live in frontend as JSON/arrays** (not stored tables)
* **Handles semantic mismatches** between similar course names

