project_root/
│
├── .env                              # Your provided environment variables
├── requirements.txt                  # Dependencies
├── results/                          # To store JSON logs
│   └── responses.json
│
├── src/
│   ├── app/
│   │   ├── main.py                   # Flask app entry point
│   │   ├── routes.py                 # Flask routes
│   │   ├── query_handler.py          # Core logic (LLM + DB query execution)
│   │   ├── schema_loader.py          # Loads schema/sample data for LLM
│   │   ├── db_connection.py          # MongoDB client
│   │   ├── response_formatter.py     # Converts different schemas into common format
│   │   └── utils.py                  # Helper functions (logging, etc.)
│   │
│   └── tests/                        # Test cases
│       ├── test_api.py
│       └── test_query_generation.py
│
└── README.md
