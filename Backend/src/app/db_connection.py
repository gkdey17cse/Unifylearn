# src/app/db_connection.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()


def get_env_or_raise(var_name):
    value = os.getenv(var_name)
    if not value:
        raise EnvironmentError(f"Missing required environment variable: {var_name}")
    return value


# Create separate clients for each cluster
coursera_client = MongoClient(get_env_or_raise("MONGO_URI_COURSERA"))
udacity_client = MongoClient(get_env_or_raise("MONGO_URI_UDACITY"))
simplilearn_client = MongoClient(get_env_or_raise("MONGO_URI_SIMPLILEARN"))
futurelearn_client = MongoClient(get_env_or_raise("MONGO_URI_FUTURELEARN"))

# Map each provider to its specific database in its specific cluster
dbMap = {
    "coursera": coursera_client[get_env_or_raise("MONGO_DB_COURSERA")],
    "udacity": udacity_client[get_env_or_raise("MONGO_DB_UDACITY")],
    "simplilearn": simplilearn_client[get_env_or_raise("MONGO_DB_SIMPLILEARN")],
    "futurelearn": futurelearn_client[get_env_or_raise("MONGO_DB_FUTURELEARN")],
}

# Collection names remain the same
COLLECTION_MAP = {
    "coursera": get_env_or_raise("MONGO_COLLECTION_COURSERA"),
    "udacity": get_env_or_raise("MONGO_COLLECTION_UDACITY"),
    "simplilearn": get_env_or_raise("MONGO_COLLECTION_SIMPLILEARN"),
    "futurelearn": get_env_or_raise("MONGO_COLLECTION_FUTURELEARN"),
}

# Optional: Store clients for health checks or cleanup
CLIENT_MAP = {
    "coursera": coursera_client,
    "udacity": udacity_client,
    "simplilearn": simplilearn_client,
    "futurelearn": futurelearn_client,
}


# NEW: Initialize database function
def initialize_db():
    """
    Initialize database connections and test them
    Returns: True if all connections are successful
    """
    try:
        print("🔌 Testing MongoDB connections...")

        # Test each client connection
        for provider, client in CLIENT_MAP.items():
            try:
                # Ping the database to test connection
                client.admin.command("ping")
                print(f"   ✅ {provider.capitalize()} connection successful")
            except Exception as e:
                print(f"   ❌ {provider.capitalize()} connection failed: {e}")
                raise ConnectionError(f"{provider} database connection failed")

        print("✅ All MongoDB connections established successfully!")
        return True

    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise


def get_collection(provider):
    """
    Returns the MongoDB collection object for the given provider.
    """
    db = dbMap.get(provider)
    collection_name = COLLECTION_MAP.get(provider)
    if db is None or collection_name is None:
        raise ValueError(f"Invalid provider: {provider}")
    return db[collection_name]


def close_all_clients():
    """
    Closes all MongoDB client connections.
    """
    for client in CLIENT_MAP.values():
        client.close()
