from pymongo import MongoClient
import json
import pprint

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["Money_control"]
collection = db["myNewCollection1"]

# Fetch data from MongoDB
cursor = collection.find()
records = list(cursor)

print(f"Found {len(records)} records in MongoDB")

# Print the structure of the first record (if any)
if records:
    print("\nStructure of the first record:")
    pprint.pprint(records[0])
    
    # Check if 'companies' key exists
    if 'companies' in records[0]:
        print("\nCompanies found in the record:", list(records[0]['companies'].keys())[:5], "...")
        
        # Print sample data for first company
        first_company = list(records[0]['companies'].keys())[0]
        print(f"\nSample data for {first_company}:")
        pprint.pprint(records[0]['companies'][first_company])
    else:
        print("\nWARNING: 'companies' key not found in the record!")
        print("Keys in record:", list(records[0].keys()))
else:
    print("No records found in the collection.")

# List all collections in the database
print("\nAll collections in the database:")
print(db.list_collection_names())

# Try to discover the correct structure
print("\nAnalyzing database structure...")
for collection_name in db.list_collection_names():
    sample_collection = db[collection_name]
    sample_docs = list(sample_collection.find().limit(1))
    
    if sample_docs:
        print(f"\nCollection '{collection_name}' has {sample_collection.count_documents({})} documents")
        print(f"Sample document keys: {list(sample_docs[0].keys())}")
        
        # Check for nested structure that might contain stock data
        for key in sample_docs[0].keys():
            if isinstance(sample_docs[0][key], dict):
                print(f"  Nested dictionary found in key '{key}': {list(sample_docs[0][key].keys())[:5]}...")