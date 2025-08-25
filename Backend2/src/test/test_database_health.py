# src/test/test_cluster_connectivity.py
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure, ConfigurationError
from dotenv import load_dotenv

load_dotenv()


def test_cluster_connection(connection_string, db_name, provider_name):
    """Test connection to a specific MongoDB cluster"""
    try:
        print(f"\n🔍 Testing {provider_name} cluster connection...")
        print(
            f"Connection string: {connection_string.split('@')[1] if '@' in connection_string else connection_string}"
        )

        # Create client and test connection
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)

        # Test connection by pinging the database
        client.admin.command("ping")
        print(f"✅ {provider_name}: Connection successful!")

        # Test database access
        db = client[db_name]
        collections = db.list_collection_names()
        print(f"✅ {provider_name}: Database '{db_name}' accessible")
        print(f"   Collections found: {collections}")

        # Test collection access (if collection exists)
        if collections:
            collection = db[collections[0]]
            count = collection.count_documents({})
            print(
                f"✅ {provider_name}: Collection '{collections[0]}' has {count} documents"
            )

        client.close()
        return True

    except ConnectionFailure as e:
        print(f"❌ {provider_name}: Connection failed - {e}")
        return False
    except OperationFailure as e:
        print(f"❌ {provider_name}: Authentication failed - {e}")
        return False
    except ConfigurationError as e:
        print(f"❌ {provider_name}: Configuration error - {e}")
        return False
    except Exception as e:
        print(f"❌ {provider_name}: Unexpected error - {e}")
        return False


def main():
    print("🚀 Testing MongoDB Cluster Connectivity")
    print("=" * 50)

    # Test each cluster
    results = {}

    # Coursera Cluster
    results["coursera"] = test_cluster_connection(
        os.getenv("MONGO_URI_COURSERA"), os.getenv("MONGO_DB_COURSERA"), "Coursera"
    )

    # Udacity Cluster
    results["udacity"] = test_cluster_connection(
        os.getenv("MONGO_URI_UDACITY"), os.getenv("MONGO_DB_UDACITY"), "Udacity"
    )

    # Simplilearn Cluster
    results["simplilearn"] = test_cluster_connection(
        os.getenv("MONGO_URI_SIMPLILEARN"),
        os.getenv("MONGO_DB_SIMPLILEARN"),
        "Simplilearn",
    )

    # FutureLearn Cluster
    results["futurelearn"] = test_cluster_connection(
        os.getenv("MONGO_URI_FUTURELEARN"),
        os.getenv("MONGO_DB_FUTURELEARN"),
        "FutureLearn",
    )

    print("\n" + "=" * 50)
    print("📊 Connection Test Summary:")
    print("=" * 50)

    success_count = sum(results.values())
    total_count = len(results)

    for provider, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{provider.upper():<15}: {status}")

    print(f"\nOverall: {success_count}/{total_count} clusters connected successfully")

    if success_count == total_count:
        print(
            "🎉 All clusters are accessible! You can proceed with multi-cluster setup."
        )
    else:
        print("⚠️  Some clusters failed. Check your connection strings and credentials.")


if __name__ == "__main__":
    main()
