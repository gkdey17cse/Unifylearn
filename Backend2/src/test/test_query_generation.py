import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB connection
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)

# Databases and collections from .env
databases = {
    os.getenv("MONGO_DB_COURSERA"): os.getenv("MONGO_COLLECTION_COURSERA"),
    os.getenv("MONGO_DB_FUTURELEARN"): os.getenv("MONGO_COLLECTION_FUTURELEARN"),
    os.getenv("MONGO_DB_SIMPLILEARN"): os.getenv("MONGO_COLLECTION_SIMPLILEARN"),
    os.getenv("MONGO_DB_UDACITY"): os.getenv("MONGO_COLLECTION_UDACITY"),
}

# Fetch sample docs
for db_name, collection_name in databases.items():
    try:
        db = client[db_name]
        collection = db[collection_name]

        # Fetch 5 random documents
        sample_docs = list(collection.aggregate([{"$sample": {"size": 5}}]))

        print(f"\n--- Sample from {db_name}.{collection_name} ---")
        for doc in sample_docs:
            print({
                "Title": doc.get("Title"),
                "Short Intro": doc.get("Short Intro"),
                "URL": doc.get("URL")
            })

    except Exception as e:
        print(f"Error fetching data from {db_name}.{collection_name}: {e}")
