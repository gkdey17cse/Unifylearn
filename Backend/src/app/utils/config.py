# src/app/utils/config.py
# central place for DB names and defaults so all files use the same names.
import os
from dotenv import load_dotenv

load_dotenv()

# Connection string: prefer MONGO_URI env var
MONGO_URI = os.getenv("MONGO_URI")  # REQUIRED in your .env

# Database names (defaults match what you used when inserting CSVs)
MONGO_DB_COURSERA = os.getenv("MONGO_DB_COURSERA", "CourseraDB")
MONGO_DB_FUTURELEARN = os.getenv("MONGO_DB_FUTURELEARN", "FutureLearnDB")
MONGO_DB_SIMPLILEARN = os.getenv("MONGO_DB_SIMPLILEARN", "SimplilearnDB")
MONGO_DB_UDACITY = os.getenv("MONGO_DB_UDACITY", "UdacityDB")

# Collections (defaults used when you inserted)
COLL_COURSERA = os.getenv("COLL_COURSERA", "Coursera")
COLL_FUTURELEARN = os.getenv("COLL_FUTURELEARN", "FutureLearn")
COLL_SIMPLILEARN = os.getenv("COLL_SIMPLILEARN", "Simplilearn")
COLL_UDACITY = os.getenv("COLL_UDACITY", "Udacity")

# Execution params
DEFAULT_PER_PROVIDER_LIMIT = int(os.getenv("DEFAULT_PER_PROVIDER_LIMIT", "20"))
MAX_PER_PROVIDER_LIMIT = int(os.getenv("MAX_PER_PROVIDER_LIMIT", "100"))

# Output dir
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./results")
