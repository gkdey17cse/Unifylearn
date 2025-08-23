IIAProject/
│
├── Backend/
│   ├── app.py                     # Main Flask/FastAPI backend
│   ├── config.py                  # Configuration (MongoDB URI, API keys, etc.)
│   ├── requirements.txt           # Python dependencies
│   ├── .env                       # Environment variables (Mongo URI, API Keys)
│   │
│   ├── db/
│   │   ├── mongo_connection.py    # MongoDB connection setup
│   │   ├── ingestion/
│   │   │   ├── ingest_csv.py      # Script to load all 4 CSVs into MongoDB
│   │   │   └── clean_data.py      # Optional preprocessing
│   │   └── schemas/               # MongoDB collection schemas (if using Pydantic)
│   │
│   ├── routes/
│   │   ├── query_routes.py        # Handles /query API
│   │   ├── ingestion_routes.py    # (Optional) API for reloading data
│   │   └── health_check.py        # /health endpoint
│   │
│   ├── services/
│   │   ├── query_engine.py        # Core logic for querying MongoDB
│   │   ├── federated_search.py    # Future: multi-database aggregator
│   │   ├── ranking.py             # LLM-based ranking / scoring
│   │   └── query_generator.py     # (Optional) Query templates for testing
│   │
│   ├── utils/
│   │   ├── logger.py              # Central logging
│   │   ├── file_handler.py        # Save query results to JSON
│   │   └── response_formatter.py  # Format API outputs
│   │
│   └── results/                   # Stores JSON outputs for each query
│
├── Data/
│   ├── raw/                       # Original CSVs for the 4 databases
│   │   ├── coursera_data.csv
│   │   ├── edx_data.csv
│   │   ├── udemy_data.csv
│   │   └── linkedin_learning.csv
│   │
│   └── processed/                 # Cleaned CSVs before ingestion
│
├── Frontend/                      # (Optional, for later UI)
│   ├── index.html
│   ├── app.js
│   └── styles.css
│
└── README.md                      # Project documentation
