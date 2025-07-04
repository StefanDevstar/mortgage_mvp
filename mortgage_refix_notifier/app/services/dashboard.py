from flask import request
import hashlib
from pymongo import MongoClient
from app.config import Config
from datetime import datetime

client = MongoClient(Config.MONGO_URI)
print("Config.MONGO_URI", Config.MONGO_URI)
db = client["mortgage"]
jobs_collection = db.jobs  # Reference the 'jobs' collection

def getMetrics():
    jobs_count = jobs_collection.count_documents({})
    
    # Define the filter to exclude jobs with state 'AWAITING_BROKER_REVIEW'
    filter_criteria = {'state': {'$ne': 'AWAITING_BROKER_REVIEW'}}
    # Get the count of documents (jobs) that do not have the state 'AWAITING_BROKER_REVIEW'
    refix_jobs_count = jobs_collection.count_documents(filter_criteria)

    filter_criteria = {'state': {'$ne': 'AWAITING_CLIENT_RESPONSE'}}
    # Get the count of documents (jobs) that do not have the state 'AWAITING_BROKER_REVIEW'
    foolowup_jobs_count = jobs_collection.count_documents(filter_criteria)


    jobs_cursor = jobs_collection.find()

    system_logs = db.logs.find()

    return {
        "TotalRefix": jobs_count,
        "RefixRate": f"{refix_jobs_count/jobs_count *100}%",
        "Follow-Up Cadence": foolowup_jobs_count,
        "SystemLogs": system_logs
    }

def saveLog(message):
    # Create a log entry with the current timestamp
    log_entry = {
        "message": message,
        "timestamp": datetime.now()  # Current date and time
    }

    # Insert the log entry into the collection
    result = db.logs.insert_one(log_entry)