import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')

DB = os.getenv('DB_NAME', 'sample_mflix')

mongo_client = MongoClient(URI)

db = mongo_client[DB]

movie_collection = db["movies"]