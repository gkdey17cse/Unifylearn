project_root/
│
├── .env
├── requirements.txt
├── results/
│   └── responses.json
│
├── src/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes.py
│   │   ├── query_handler.py
│   │   ├── schema_loader.py
│   │   ├── db_connection.py
│   │   ├── response_formatter.py
│   │   ├── utils.py
│   │   ├── query_generator/
│   │   │   ├── __init__.py
│   │   │   ├── llm_query_builder.py
│   │   │   └── query_translator.py
│   │   ├── query_executor/
│   │   │   ├── __init__.py
│   │   │   └── provider_executor.py
│   │   └── results/
│   │       ├── __init__.py
│   │       └── saver.py
│   │
│   └── tests/
│       ├── test_api.py
│       └── test_query_generation.py
│
└── README.md



Key Intelligence Added:
Query Type Detection: Automatically detects category-based, technology-based, and topic-based queries

Context Preservation: Uses word boundaries (\b) and preserves technical phrases

Smart Field Selection: Chooses appropriate fields based on query type

Provider Awareness: Only queries relevant providers mentioned in the query

Limit Handling: Properly handles numeric limits like "5 courses"