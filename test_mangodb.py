from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

# Use full Windows path with raw string (to avoid escape sequences)
load_dotenv(dotenv_path=r"C:\ENGINEERING PROJECTS\Network_Security\.env")

uri = os.getenv("MANGODB_DB_URL")

if uri is None:
    raise ValueError("❌ MONGO_URI not loaded. Check .env file and path.")

print("✅ Loaded MONGO_URI:", uri)


# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)