import pandas as pd
from pymongo import MongoClient
import os

# Load environment variables
mongoUri="mongodb+srv://gour24035:iia2025@iiaproject.qeemfj8.mongodb.net/?retryWrites=true&w=majority&appName=IIAProject"
# mongoUri = os.getenv("MONGODB_URI")

# Connect to MongoDB
client = MongoClient(mongoUri)

# Define your databases and corresponding CSV files
dbCollections = {
    "CourseraDB": {"Coursera": "OnlineCoursera.csv"},
    "FutureLearnDB": {"FutureLearn": "OnlineFutureLearn.csv"},
    "SimplilearnDB": {"Simplilearn": "OnlineSimplilearn.csv"},
    "UdacityDB": {"Udacity": "OnlineUdacity.csv"}
}

for dbName, collections in dbCollections.items():
    db = client[dbName]
    for collectionName, csvPath in collections.items():
        print(f"Inserting {csvPath} into {dbName}.{collectionName}")
        df = pd.read_csv(csvPath)
        data = df.to_dict(orient="records")  # Convert DataFrame to list of dicts
        db[collectionName].insert_many(data)

print("All CSV files inserted successfully!")
