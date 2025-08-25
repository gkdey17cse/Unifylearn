Project/
  ├── Backend/
  |     ├── .env
  |     ├── requirements.txt
  |     ├── results/
  |     │ └── responses.json
  |     │
  |     ├── src/
  |     │ ├── app/
  |     │ │ ├── main.py
  |     │ │ ├── routes.py
  |     │ │ ├── query_handler.py
  |     │ │ ├── schema_loader.py
  |     │ │ ├── db_connection.py
  |     │ │ ├── response_formatter.py
  |     | | ├── universal_schema.py # NEW: Standard schema definition
  |     │ │ ├── utils.py
  |     | | ├── data_enrichment/ # NEW: Data standardization and enrichment
  |     | | │ ├── **init**.py
  |     | | │ ├── llm_enricher.py # LLM-based data completion
  |     | | │ └── uniform_formatter.py # Universal schema formatting
  |     │ │ ├── query_generator/
  |     │ │ │ ├── **init**.py
  |     │ │ │ ├── llm_query_builder.py
  |     │ │ │ └── query_translator.py
  |     │ │ ├── query_executor/
  |     │ │ │ ├── **init**.py
  |     │ │ │ └── provider_executor.py
  |     │ │ └── results/
  |     │ │ ├── **init**.py
  |     │ │ └── saver.py
  |     │ │
  |     │ └── tests/
  |     │ ├── test_api.py
  |     │ └── test_query_generation.py
  |     │
  |     └── README.md
  ├── Frontend/
  |     ├── app.js (Express server)
  |     ├── package.json
  |     ├── package-lock.json
  |     ├── node_modules
  |     ├── .env
  |     ├── views/
  |     │   ├── index.ejs (main homepage)
  |     │   └── partials/
  |     │       ├── header.ejs
  |     │       ├── footer.ejs
  |     │       └── chatbot.ejs
  |     ├── public/
  |     │   ├── css/
  |     │   │   └── style.css
  |     │   ├── js/
  |     │   │   └── script.js
  |     │   └── assets/
  |     │       └── (images, etc.)
  |     └── routes/
  |         └── index.js (API route handlers)
  ├── .gitignore
  ├── IIA/
  ├── Plans/
  └── README.md



POST /query - Process user query, save 4 files, return results

GET /results - List all timestamp directories

GET /results/<timestamp> - Get polished results for frontend

GET /results/<timestamp>/files - List all 4 files in a directory

GET /results/<timestamp>/<filename> - Download specific JSON file


