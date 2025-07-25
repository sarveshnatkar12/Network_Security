import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import certifi

load_dotenv()
uri = os.getenv("MONGO_DB_URL")

print(f"✅ Loaded MONGO_URI: {uri}")

# Use certifi's certificate file to avoid SSL issues
client = MongoClient(uri, server_api=ServerApi('1'), tlsCAFile=certifi.where())

try:
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB Atlas")
except Exception as e:
    print("❌ Connection failed:", e)
