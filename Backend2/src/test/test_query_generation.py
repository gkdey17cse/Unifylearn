import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define cluster configurations with their respective connection strings
clusters = {
    "coursera": {
        "uri": os.getenv("MONGO_URI_COURSERA"),
        "db": os.getenv("MONGO_DB_COURSERA"),
        "collection": os.getenv("MONGO_COLLECTION_COURSERA"),
    },
    "futurelearn": {
        "uri": os.getenv("MONGO_URI_FUTURELEARN"),
        "db": os.getenv("MONGO_DB_FUTURELEARN"),
        "collection": os.getenv("MONGO_COLLECTION_FUTURELEARN"),
    },
    "simplilearn": {
        "uri": os.getenv("MONGO_URI_SIMPLILEARN"),
        "db": os.getenv("MONGO_DB_SIMPLILEARN"),
        "collection": os.getenv("MONGO_COLLECTION_SIMPLILEARN"),
    },
    "udacity": {
        "uri": os.getenv("MONGO_URI_UDACITY"),
        "db": os.getenv("MONGO_DB_UDACITY"),
        "collection": os.getenv("MONGO_COLLECTION_UDACITY"),
    },
}


def fetch_data_from_clusters():
    """Fetch sample data from all MongoDB clusters"""
    results = {}

    for provider, config in clusters.items():
        try:
            print(f"\n🔍 Fetching data from {provider.upper()} cluster...")

            # Create a separate client for each cluster
            client = MongoClient(config["uri"], serverSelectionTimeoutMS=10000)

            # Test connection first
            client.admin.command("ping")

            # Access database and collection
            db = client[config["db"]]
            collection = db[config["collection"]]

            # Fetch 5 random documents
            sample_docs = list(collection.aggregate([{"$sample": {"size": 5}}]))

            print(
                f"✅ Successfully fetched {len(sample_docs)} documents from {provider}"
            )

            # Store results
            results[provider] = {
                "count": len(sample_docs),
                "documents": sample_docs,
                "status": "success",
            }

            # Display sample
            print(
                f"\n--- Sample from {provider.upper()} ({config['db']}.{config['collection']}) ---"
            )
            for i, doc in enumerate(sample_docs, 1):
                print(f"{i}. Title: {doc.get('Title', 'N/A')}")
                print(f"   Intro: {doc.get('Short Intro', 'N/A')[:100]}...")
                print(f"   URL: {doc.get('URL', 'N/A')}")
                print()

            client.close()

        except Exception as e:
            print(f"❌ Error fetching data from {provider}: {e}")
            results[provider] = {
                "count": 0,
                "documents": [],
                "status": f"error: {str(e)}",
            }

    return results


def main():
    print("🚀 Fetching Data from Multiple MongoDB Clusters")
    print("=" * 60)

    results = fetch_data_from_clusters()

    print("\n" + "=" * 60)
    print("📊 Data Fetching Summary:")
    print("=" * 60)

    success_count = sum(1 for r in results.values() if r["status"] == "success")

    for provider, result in results.items():
        status = "✅ SUCCESS" if result["status"] == "success" else "❌ FAILED"
        print(f"{provider.upper():<15}: {status} ({result['count']} documents)")

    print(
        f"\nOverall: {success_count}/{len(clusters)} clusters fetched data successfully"
    )

    if success_count == len(clusters):
        print("🎉 All clusters are working correctly! Data fetching is operational.")
    else:
        print("⚠️  Some clusters failed. Check your data and collection names.")


if __name__ == "__main__":
    main()
