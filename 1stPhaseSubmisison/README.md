# UnifyLearn: Intelligent Cross-Platform Course Discovery Engine

## Project Overview

UnifyLearn is an AI-powered unified course search system that interprets natural language queries to retrieve and standardize learning content from multiple platforms including Coursera, Udemy, Simplilearn, and FutureLearn. The system integrates structured and unstructured data, dynamically generates database queries, and delivers context-aware learning recommendations through a universal schema.

## Project Structure (Required Files Only)

```
Backend/
├── .env                    # Environment variables (API keys, DB connections)
├── requirements.txt        # Python dependencies
├── main.py                # Main application entry point
└── src/
    └── app/
        ├── schema_loader.py           # Loads and manages database schemas
        └── query_generator/
            ├── llm_query_builder.py   # LLM-based natural language query processing
            └── query_translator.py    # Translates queries to MongoDB format
```

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- MongoDB instances (Coursera_DB, FutureLearn_DB, Udacity_DB, Simplilearn_DB)
- Google Gemini API key

### Step 1: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Create or update the `.env` file with the following variables:

```env
GEMINI_API_KEY=your_gemini_api_key_here
MONGO_URI_Coursera_DB=your_mongodb_connection_string
MONGO_URI_FutureLearn_DB=your_mongodb_connection_string
MONGO_URI_Udacity_DB=your_mongodb_connection_string
MONGO_URI_Simplilearn_DB=your_mongodb_connection_string
```

### Step 4: Run the Application

```bash
python main.py
```

## Directory Structure Details

- **main.py**: Main application entry point that initializes the federated query processor and handles the core application logic
- **src/app/schema_loader.py**: Handles loading and mapping of unified schema across all educational platforms, ensuring consistent data representation
- **src/app/query_generator/llm_query_builder.py**: Processes natural language queries using Gemini LLM to extract intent, filters, and keywords
- **src/app/query_generator/query_translator.py**: Translates logical queries to platform-specific MongoDB queries and handles schema alignment

## Dependencies

The `requirements.txt` file includes:
- `pymongo` - MongoDB database connectivity
- `google-generativeai` - Gemini LLM integration
- `python-dotenv` - Environment variable management
- Additional dependencies for data processing and API handling

## Core Features

- **Natural Language Query Processing**: Understands user intent using Gemini LLM for semantic parsing
- **Cross-Platform Federation**: Searches across 4 MongoDB clusters simultaneously (Coursera, FutureLearn, Udacity, Simplilearn)
- **Schema Standardization**: Unified metadata mapping across different educational platforms
- **Real-time Virtualization**: No pre-stored results, ensuring data freshness across all platforms
- **SPJ Query Support**: Select-Project-Join queries for structured filtering and course retrieval

## Supported Query Types

The system currently supports SPJ (Select-Project-Join) queries including:

- "Find Data Science courses with duration less than 3 months"
- "List Cloud courses covering AWS and Azure from Udacity platform"
- "Retrieve courses with the highest ratings across all platforms"
- "Fetch Data Science courses requiring Python and R programming skills"

## System Architecture

The current implementation follows a virtualization-based federated query architecture:
- Queries are executed in real-time across multiple MongoDB clusters
- No pre-storing or caching of intermediate results
- Dynamic handling of frequently changing fields (ratings, views, course details)
- Compatible with MongoDB's flexible JSON schema and nested document structures

## Current Capabilities

- SPJ (Select-Project-Join) query support across multiple platforms
- Natural language to MongoDB query translation
- Cross-platform federated search with unified results
- LLM-based query understanding and semantic enrichment
- Real-time data virtualization ensuring up-to-date information

## Future Enhancements

Planned improvements include:
- Distributed query execution for improved performance
- Aggregate query support (AVG, MAX, COUNT, ranking)
- Hybrid architecture combining virtualization and materialization
- Enhanced semantic search capabilities
- Support for advanced cross-platform analytics

## Documentation

For detailed technical documentation, architecture diagrams, and implementation details, refer to the project report (Report.pdf) in the repository.

## Technical Specifications

- **Backend Framework**: Python
- **Database**: MongoDB (multiple clusters)
- **LLM Integration**: Google Gemini AI Studio API
- **Query Processing**: Federated query execution
- **Schema Management**: Unified metadata standardization

---

**Group No: 18**  

*Gour Krishna Dey (MT24035) & Parul (MT24128)*  
*Department of Computer Science, IIIT-Delhi*