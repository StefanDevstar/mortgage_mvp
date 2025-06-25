from flask_pymongo import PyMongo
from config import Config
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson.objectid import ObjectId
import crm_agent, valuation_agent, rate_parser, economic_agent, repayment_agent, email_agent
import gmail_client

# Setup Mongo
client = MongoClient(Config.MONGO_URI)
db = client.get_default_database()

def process_all_jobs():
    now = datetime.utcnow()
    # 1. Draft initial email for broker
    for job in db.jobs.find({'state': 'DRAFT_FOR_BROKER'}):
        email_body = email_agent.draft_broker_email(job)
        gmail_client.send_email(to_address=gmail_client.BROKER_EMAIL, subject=f"Refix Review - {job['client_name']}", body=email_body)
        db.jobs.update_one({'_id': job['_id']}, {'$set': {'state': 'AWAITING_BROKER_REVIEW', 'last_sent_at': now}})

    # 2. Broker reminder
    for job in db.jobs.find({'state': 'AWAITING_BROKER_REVIEW', 'last_sent_at': {'$lte': now - timedelta(days=2)}}):
        gmail_client.send_email(to_address=gmail_client.BROKER_EMAIL, subject="Reminder: Refix review pending", body=f"Please review job {job['_id']}")
        db.jobs.update_one({'_id': job['_id']}, {'$set': {'last_sent_at': now}})

    # 3. Send follow-up to client if no response
    for job in db.jobs.find({'state': 'FIRST_EMAIL_SENT', 'next_action_at': {'$lte': now}}):
        email_body = email_agent.draft_client_followup(job)
        gmail_client.send_email(to_address=job.get('client_email'), subject="Refix Reminder", body=email_body)
        next_date = now + timedelta(days=30)
        db.jobs.update_one({'_id': job['_id']}, {'$set': {'next_action_at': next_date}})

    # 4. Check for client replies
    replies = gmail_client.fetch_unread_replies()
    for reply in replies:
        job_id = reply['in_reply_to_job']
        job = db.jobs.find_one({'_id': ObjectId(job_id)})
        if job:
            email_body = email_agent.draft_second_email(job, reply['content'])
            gmail_client.send_email(to_address=gmail_client.BROKER_EMAIL, subject=f"Second Email Review - {job['client_name']}", body=email_body)
            db.jobs.update_one({'_id': job['_id']}, {'$set': {'state': 'DRAFT_SECOND_FOR_BROKER'}})

def send_client_email(job):
    # Orchestrate agents
    client = crm_agent.get_client_data(job['client_id'])
    valuation = valuation_agent.fetch_valuation(client['address'])
    rates = rate_parser.parse_rate_card('latest_rate_card.pdf')
    insights = economic_agent.get_market_insights()
    scenarios = repayment_agent.build_repayment_scenarios(client['loan_amount'], rates)
    email_body = email_agent.draft_client_email(client, valuation, rates, insights, scenarios)
    gmail_client.send_email(to_address=client.get('client_email'), subject="Your Mortgage Refix Options", body=email_body)
    db.jobs.update_one({'_id': job['_id']}, {'$set': {'client_email': client.get('client_email')}})