from flask_pymongo import PyMongo
from app.config import Config
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from agents import crm_monitor, property_valuation, rate_card_parser, economic_summary, repayment_scenarios, email_generator
from app import gmail_client

# Setup Mongo
client = MongoClient(Config.MONGO_URI)
db = client["mortgage"]

def process_all_jobs():
      # ─── Step 0: Create new jobs for any clients whose refix is due ───
    for client_info in crm_monitor.check_mortgage_expiry():
        # Skip if there's already an active job for this client
        exists = db.jobs.find_one({
            'client_id': client_info['client_id'],
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
                'client_id':      client_info['client_id'],
                'client_name':    client_info['client_name'],
                'address':        client_info['address'],
                'loan_amount':    client_info['loan_amount'],
                'expiry_date':    client_info['mortgage_end'],
                'state':          'DRAFT_FOR_BROKER',
                'last_sent_at':   None,
                'next_action_at': None,
            }
            db.jobs.insert_one(job)
            print(f"Created job for client {client_info['client_id']}")


    now = datetime.utcnow()
    # 1. Draft initial email for broker
    for job in db.jobs.find({'state': 'DRAFT_FOR_BROKER'}):
        email_body = email_generator.draft_broker_email(job)
        gmail_client.send_email(to_address=gmail_client.BROKER_EMAIL, subject=f"Refix Review - {job['client_name']}", body=email_body)
        db.jobs.update_one({'_id': job['_id']}, {'$set': {'state': 'AWAITING_BROKER_REVIEW', 'last_sent_at': now}})

    # 2. Broker reminder
    for job in db.jobs.find({'state': 'AWAITING_BROKER_REVIEW', 'last_sent_at': {'$lte': now - timedelta(days=2)}}):
        gmail_client.send_email(to_address=gmail_client.BROKER_EMAIL, subject="Reminder: Refix review pending", body=f"Please review job {job['_id']}")
        db.jobs.update_one({'_id': job['_id']}, {'$set': {'last_sent_at': now}})

    # 3. Send follow-up to client if no response
    for job in db.jobs.find({'state': 'FIRST_EMAIL_SENT', 'next_action_at': {'$lte': now}}):
        email_body = email_generator.draft_client_followup(job)
        gmail_client.send_email(to_address=job.get('client_email'), subject="Refix Reminder", body=email_body)
        next_date = now + timedelta(days=30)
        db.jobs.update_one({'_id': job['_id']}, {'$set': {'next_action_at': next_date}})

    # 4. Check for client replies
    replies = gmail_client.fetch_unread_replies()
    for reply in replies:
        job_id = reply['in_reply_to_job']
        job = db.jobs.find_one({'_id': ObjectId(job_id)})
        if job:
            email_body = email_generator.generate_second_email(job, reply['content'])
            gmail_client.send_email(to_address=gmail_client.BROKER_EMAIL, subject=f"Second Email Review - {job['client_name']}", body=email_body)
            db.jobs.update_one({'_id': job['_id']}, {'$set': {'state': 'DRAFT_SECOND_FOR_BROKER'}})
