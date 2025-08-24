from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

mongoUri = os.getenv("MONGO_URI")
client = MongoClient(mongoUri)

# Use the specific database names from environment variables
dbMap = {
    "coursera": client[os.getenv("MONGO_DB_COURSERA")],
    "futurelearn": client[os.getenv("MONGO_DB_FUTURELEARN")],
    "simplilearn": client[os.getenv("MONGO_DB_SIMPLILEARN")],
    "udacity": client[os.getenv("MONGO_DB_UDACITY")],
}

# Collection names from environment variables
COLLECTION_MAP = {
    "coursera": os.getenv("MONGO_COLLECTION_COURSERA"),
    "futurelearn": os.getenv("MONGO_COLLECTION_FUTURELEARN"),
    "simplilearn": os.getenv("MONGO_COLLECTION_SIMPLILEARN"),
    "udacity": os.getenv("MONGO_COLLECTION_UDACITY"),
}
