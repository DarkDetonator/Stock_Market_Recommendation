

import os
import json
from pymongo import MongoClient

# Folder containing all JSON files
folder_path = 'NIFTY50_Data\Thirdmont'  # Replace with your full folder path if needed

# MongoDB connection

client = MongoClient('mongodb://localhost:27017')  # Update with your URI if remote
db = client['Money_control']  # Replace with your DB name
collection = db['myNewCollection1']  # Replace with your collection name

# Loop through each file in the folder
for filename in os.listdir(folder_path):
    if filename.endswith('.json'):
        file_path = os.path.join(folder_path, filename)
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                
                # Insert data depending on its structure
                if isinstance(data, list):
                    collection.insert_many(data)
                else:
                    collection.insert_one(data)

                print(f"✅ Inserted data from {filename}")
        except Exception as e:
            print(f"❌ Error inserting {filename}: {e}")

print("🎉 All files processed.")
