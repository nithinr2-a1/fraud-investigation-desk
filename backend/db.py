from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Read values from .env
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# Connect to MongoDB Atlas
client = MongoClient(MONGO_URI)

db = client[DATABASE_NAME]

# Collections
claims = db["claims"]
users = db["users"]
cases = db["cases"]
transactions = db["transactions"]
predictions = db["predictions"]
evidence = db["evidence"]
notes = db["notes"]
audit_logs = db["audit_logs"]
suspects = db["suspects"]

client.admin.command("ping")
print("✅ Connected to MongoDB Atlas")