- Directory structure for the Backend
```bash 
Backend/
├── .env
├── requirements.txt
├── main.py
└── src/
    └── app/
        ├── schema_loader.py
        └── query_generator/
            ├── llm_query_builder.py
            └── query_translator.py
```
Key Intelligence Added:
Query Type Detection: Automatically detects category-based, technology-based, and topic-based queries

Context Preservation: Uses word boundaries (\b) and preserves technical phrases

Smart Field Selection: Chooses appropriate fields based on query type

Provider Awareness: Only queries relevant providers mentioned in the query

Limit Handling: Properly handles numeric limits like "5 courses"

- Common Strcuture

```bash
Title	URL	Short Intro	Category	Language	Skills	Instructors	Duration	Site	Level	Number of Reviews	Prequisites	What you learn	Price
```

Perfect! Your directory structure is absolutely correct. Here's the comprehensive documentation:

## 📁 Directory Structure & File Documentation

### **Core Application Files**

| File                    | Purpose                                                     |
| ----------------------- | ----------------------------------------------------------- |
| `main.py`               | Flask app entry point, initializes the web server           |
| `routes.py`             | Defines API endpoints (`/health`, `/query`)                 |
| `db_connection.py`      | MongoDB connection setup with provider-specific databases   |
| `schema_loader.py`      | Provides schema definitions and sample data for LLM context |
| `universal_schema.py`   | Defines standardized course format and field mappings       |
| `response_formatter.py` | Converts raw data to unified format with LLM enrichment     |
| `utils.py`              | Common utility functions and helpers                        |

### **Query Generation Module** (`query_generator/`)

| File                   | Purpose                                                    |
| ---------------------- | ---------------------------------------------------------- |
| `llm_query_builder.py` | Uses LLM to generate MongoDB queries from natural language |
| `query_translator.py`  | Maps schema field names to actual database field names     |

### **Query Execution Module** (`query_executor/`)

| File                   | Purpose                                                    |
| ---------------------- | ---------------------------------------------------------- |
| `provider_executor.py` | Executes queries against MongoDB with intelligent fallback |

### **Data Enrichment Module** (`data_enrichment/`)

| File                   | Purpose                                                |
| ---------------------- | ------------------------------------------------------ |
| `llm_enricher.py`      | Uses LLM to fill missing fields in universal schema    |
| `uniform_formatter.py` | Converts provider-specific data to standardized format |

### **Results Module** (`results/`)

| File       | Purpose                                                 |
| ---------- | ------------------------------------------------------- |
| `saver.py` | Saves query results and debug information to JSON files |

## 🔄 End-to-End Flow (How Everything Connects)

### **API Request Flow:**

1. **User** → `POST /query` → `routes.py` → `query_handler.py`
2. **Query Handler** → `llm_query_builder.py` (Generate queries)
3. **Query Handler** → `provider_executor.py` (Execute queries)
4. **Query Handler** → `response_formatter.py` → `uniform_formatter.py` → `llm_enricher.py` (Format & enrich)
5. **Query Handler** → `saver.py` (Save results)
6. **Response** → User with standardized course data

### **Data Transformation Flow:**

```
Raw MongoDB Data
→ response_formatter.py
→ uniform_formatter.py (basic mapping)
→ llm_enricher.py (fill missing fields)
→ Universal Schema Format
→ saver.py (save as enriched_courses.json)
```

### **Query Execution Flow:**

```
Natural Language Query
→ llm_query_builder.py (LLM generates query)
→ query_translator.py (field name mapping)
→ provider_executor.py (execute on MongoDB)
→ Fallback mechanism if no results
→ Return matched documents
```

## 🎯 Key Functions Overview

### **In `query_handler.py`**

- `processUserQuery()`: Main orchestrator - handles the entire query pipeline
- `save_enriched_courses()`: Saves standardized course data

### **In `llm_query_builder.py`**

- `generate_queries()`: Converts natural language to MongoDB queries using LLM

### **In `provider_executor.py`**

- `execute_provider_query()`: Runs queries on MongoDB with smart fallback
- `build_keyword_fallback_query()`: Creates context-aware fallback queries

### **In `uniform_formatter.py`**

- `format_to_universal_schema()`: Converts raw data to standardized format

### **In `llm_enricher.py`**

- `enrich_course_data()`: Uses LLM to intelligently fill missing fields

### **In `saver.py`**

- `save_results()`: Saves debug information and query results

## 📊 Data Flow Diagram

```
User Query → API → Query Handler → LLM Query Builder → Query Translator
    ↓
Provider Executor → MongoDB → Raw Results → Response Formatter
    ↓
Uniform Formatter → LLM Enricher → Universal Format → Result Saver
    ↓
JSON Output → User Response
```

This architecture ensures that:

1. **Natural language queries** become **precise database queries**
2. **Provider-specific data** becomes **standardized information**
3. **Missing data** gets **intelligently filled** by LLM
4. **All results** are **persisted for analysis**
5. **API responses** are **consistent and complete**

The system beautifully combines LLM intelligence with database precision! 🚀
