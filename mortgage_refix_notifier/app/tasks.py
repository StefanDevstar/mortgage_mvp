from flask_pymongo import PyMongo
from app.config import Config
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from agents import crm_monitor, property_valuation, rate_card_parser, economic_summary
from agents.email_generator import email_broker_review_generator, email_second_followup_generator, email_second_followup_generator
from app import gmail_client


# Setup Mongo
client = MongoClient(Config.MONGO_URI)
db = client["mortgage"]

def process_all_jobs():
      # ─── Step 0: Create new jobs for any clients whose refix is due ───
    for client_info in crm_monitor.scrape_crm_data():
        # Skip if there's already an active job for this client
        exists = db.jobs.find_one({
            'Customer': client_info['Customer'],
            'state': {'$in': [
                'DRAFT_FOR_BROKER',
                'AWAITING_BROKER_REVIEW',
                'FIRST_EMAIL_SENT',
                'AWAITING_CLIENT_RESPONSE',
                'DRAFT_SECOND_FOR_BROKER'
            ]}
        })
        if not exists:
            job = {
                'Customer':    client_info['Customer'],
                'Address':        client_info['Address'],
                'Lender':         client_info['Lender'],
                'Loan_Amount':    client_info['Loan_Amount'],
                'Rate_Type':    client_info['Rate_Type'],
                'Expiry_Date':    client_info['Expiry_Date'],
                'state':          'DRAFT_FOR_BROKER',
                'last_sent_at':   None,
                'next_action_at': None,
            }
            db.jobs.insert_one(job)
            print(f"Created job for client {client_info['Customer']}")


    now = datetime.utcnow()
    # 1. Draft initial email for broker
    for job in db.jobs.find({'state': 'DRAFT_FOR_BROKER'}):
        email_body = email_broker_review_generator.main(job)
        gmail_client.send_email(to_address=Config.BROKER_EMAIL, subject=f"Refix Review - {job['Customer']}", body=email_body)
        db.jobs.update_one({'_id': job['_id']}, {'$set': {'state': 'AWAITING_BROKER_REVIEW', 'last_sent_at': now}})

    # 2. Broker reminder
    for job in db.jobs.find({'state': 'AWAITING_BROKER_REVIEW', 'last_sent_at': {'$lte': now - timedelta(days=2)}}):
        gmail_client.send_email(to_address=Config.BROKER_EMAIL, subject="Reminder: Refix review pending", body=f"Please review job {job['_id']}")
        db.jobs.update_one({'_id': job['_id']}, {'$set': {'last_sent_at': now}})

    # 3. Send follow-up to client if no response
    for job in db.jobs.find({'state': 'FIRST_EMAIL_SENT', 'next_action_at': {'$lte': now}}):
        email_body = email_second_followup_generator.main(job)
        gmail_client.send_email(to_address=job.get('client_email'), subject="Refix Reminder", body=email_body)
        next_date = now + timedelta(days=30)
        db.jobs.update_one({'_id': job['_id']}, {'$set': {'next_action_at': next_date}})

    # 4. Check for client replies
    replies = gmail_client.fetch_unread_replies()
    for reply in replies:
        job_id = reply['in_reply_to_job']
        job = db.jobs.find_one({'_id': ObjectId(job_id)})
        if job:
            email_body = email_second_followup_generator.main(job, reply['content'])
            gmail_client.send_email(to_address=Config.BROKER_EMAIL, subject=f"Second Email Review - {job['Customer']}", body=email_body)
            db.jobs.update_one({'_id': job['_id']}, {'$set': {'state': 'DRAFT_SECOND_FOR_BROKER'}})
