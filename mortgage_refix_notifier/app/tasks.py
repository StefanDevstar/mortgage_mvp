from flask_pymongo import PyMongo
from app.config import Config
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson.objectid import ObjectId

from agents import crm_monitor, property_valuation, rate_card_parser, economic_summary
from agents.email_generator import email_broker_review_generator, email_second_followup_generator
from app import gmail_client

# ✅ Setup MongoDB
client = MongoClient(Config.MONGO_URI)
db = client["mortgage"]

def process_all_jobs():
    # ─── Step 0: Create new jobs for any clients whose refix is due ───
    for client_info in crm_monitor.scrape_crm_data():
        job = {
            'Customer':      client_info['Customer'],
            'Address':       client_info['Address'],
            'Lender':        client_info['Lender'],
            'Loan_Amount':   client_info['Loan_Amount'],
            'Rate_Type':     client_info['Rate_Type'],
            'Expiry_Date':   client_info['Expiry_Date'],
            'client_email':  client_info.get('Email') or client_info.get('client_email'),
            'state':         'DRAFT_FOR_BROKER',
            'last_sent_at':  None,
            'next_action_at': None,
            'email_subject': None,
            'email_body_html': None
        }
        db.jobs.insert_one(job)
        print(f"✅ Created job for client {client_info['Customer']}")

    now = datetime.utcnow()

    # ─── Step 1: Draft broker-facing email (store client draft only) ───
    for job in db.jobs.find({'state': 'DRAFT_FOR_BROKER'}):
        result = email_broker_review_generator.main(job)

        if isinstance(result, dict):
            broker_subject = result.get('broker_subject')
            broker_body = result.get('broker_body')  # ✅ With buttons
            client_subject = result.get('client_subject')
            client_body = result.get('client_body')  # ✅ No buttons
        else:
            broker_subject = f"Refix Review - {job['Customer']}"
            broker_body = result
            client_subject = None
            client_body = None

        # ✅ Send broker email only
        gmail_client.send_email(
            to_address=Config.BROKER_EMAIL,
            subject=broker_subject,
            body=broker_body,
            job_id=str(job['_id']),
            is_html=True
        )

        # ✅ Save client draft to DB (but don't send yet)
        db.jobs.update_one(
            {'_id': job['_id']},
            {'$set': {
                'state': 'AWAITING_BROKER_REVIEW',
                'last_sent_at': now,
                'email_subject': client_subject,
                'email_body_html': client_body,
                'broker_subject': broker_subject,
                'broker_body_html': broker_body
            }}
        )

    # ─── Step 2: Broker reminder after 2 days ───
    for job in db.jobs.find({
        'state': 'AWAITING_BROKER_REVIEW',
        'last_sent_at': {'$lte': now - timedelta(days=2)}
    }):
        gmail_client.send_email(
            to_address=Config.BROKER_EMAIL,
            subject="Reminder: Refix review pending",
            body=f"Please review job {job['_id']}",
            job_id=str(job['_id'])
        )
        db.jobs.update_one({'_id': job['_id']}, {'$set': {'last_sent_at': now}})

    # ─── Step 3: Follow-up to client if no response ───
    for job in db.jobs.find({
        'state': 'FIRST_EMAIL_SENT',
        'next_action_at': {'$lte': now}
    }):
        subject = "Refix Reminder"
        email_body = email_second_followup_generator.main(job)

        gmail_client.send_email(
            to_address=job.get('client_email'),
            subject=subject,
            body=email_body,
            job_id=str(job['_id']),
            is_html=True,
            is_client_email=True
        )
        db.jobs.update_one({'_id': job['_id']}, {
            '$set': {
                'next_action_at': now + timedelta(days=30),
                'email_subject': subject,
                'email_body_html': email_body
            }
        })

    # ─── Step 4: Check for client replies ───
    replies = gmail_client.fetch_unread_replies()
    for reply in replies:
        job_id = reply.get('in_reply_to_job')
        if not job_id:
            continue
        try:
            job = db.jobs.find_one({'_id': ObjectId(job_id)})
            if job:
                subject = f"Second Email Review - {job['Customer']}"
                email_body = email_second_followup_generator.main(job, reply['content'])

                gmail_client.send_email(
                    to_address=Config.BROKER_EMAIL,
                    subject=subject,
                    body=email_body,
                    job_id=str(job['_id']),
                    is_html=True
                )

                db.jobs.update_one({'_id': job['_id']}, {
                    '$set': {
                        'state': 'DRAFT_SECOND_FOR_BROKER',
                        'email_subject': subject,
                        'email_body_html': email_body
                    }
                })
        except Exception as e:
            print(f"⚠️ Failed to process reply for job_id {job_id}: {e}")
