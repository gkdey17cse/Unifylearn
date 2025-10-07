# src/app/db_connection.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()


def get_env_or_raise(var_name):
    value = os.getenv(var_name)
    if not value:
        raise EnvironmentError(f"Missing environment variable: {var_name}")
    return value


coursera_client = MongoClient(get_env_or_raise("MONGO_URI_COURSERA"))
udacity_client = MongoClient(get_env_or_raise("MONGO_URI_UDACITY"))
simplilearn_client = MongoClient(get_env_or_raise("MONGO_URI_SIMPLILEARN"))
futurelearn_client = MongoClient(get_env_or_raise("MONGO_URI_FUTURELEARN"))

dbMap = {
    "coursera": coursera_client[get_env_or_raise("MONGO_DB_COURSERA")],
    "udacity": udacity_client[get_env_or_raise("MONGO_DB_UDACITY")],
    "simplilearn": simplilearn_client[get_env_or_raise("MONGO_DB_SIMPLILEARN")],
    "futurelearn": futurelearn_client[get_env_or_raise("MONGO_DB_FUTURELEARN")],
}

COLLECTION_MAP = {
    "coursera": get_env_or_raise("MONGO_COLLECTION_COURSERA"),
    "udacity": get_env_or_raise("MONGO_COLLECTION_UDACITY"),
    "simplilearn": get_env_or_raise("MONGO_COLLECTION_SIMPLILEARN"),
    "futurelearn": get_env_or_raise("MONGO_COLLECTION_FUTURELEARN"),
}


def initialize_db():
    try:
        print("Testing MongoDB connections...")

        clients = {
            "coursera": coursera_client,
            "udacity": udacity_client,
            "simplilearn": simplilearn_client,
            "futurelearn": futurelearn_client,
        }

        for provider, client in clients.items():
            try:
                client.admin.command("ping")
                print(f"{provider.capitalize()} connection successful")
            except Exception as e:
                print(f"{provider.capitalize()} connection failed: {e}")
                raise

        print("All MongoDB connections established")
        return True

    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise
