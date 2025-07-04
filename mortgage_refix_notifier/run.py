import os
from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from app.config import Config
from app.tasks import process_all_jobs
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app import gmail_client  # ✅ Make sure this works

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'app', 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'app', 'static')

app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR,
)

app.secret_key = 'mortgage_agent'
app.config.from_object(Config)

# Setup Mongo
client = MongoClient(Config.MONGO_URI)
print("Config.MONGO_URI", Config.MONGO_URI)
db = client["mortgage"]

# ─────────────────── Scheduler ────────────────────
def start_scheduler():
    print("***********Started Scheduler************")
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=process_all_jobs,
        trigger=CronTrigger(hour=2, minute=0),
        id="daily_refix_job",
        replace_existing=True
    )
    scheduler.start()

with app.app_context():
    start_scheduler()

# ─────────────── Register Blueprints ──────────────
from app.routes.admin_routes import admin_bp
app.register_blueprint(admin_bp)

# ─────────────────── ROUTES ───────────────────────
@app.route('/', methods=['GET'])
def root():
    return jsonify({'status': 'Tasks executed'}), 200

@app.route('/jobs', methods=['POST'])
def create_job():
    data = request.json
    job = {
        'client_id': data['client_id'],
        'client_name': data.get('client_name'),
        'address': data['address'],
        'loan_amount': data['loan_amount'],
        'expiry_date': datetime.fromisoformat(data['expiry_date']),
        'state': 'DRAFT_FOR_BROKER',
        'last_sent_at': None,
        'next_action_at': None,
    }
    result = db.jobs.insert_one(job)
    return jsonify({'job_id': str(result.inserted_id)}), 201

@app.route('/jobs/<job_id>/approve', methods=['POST'])
def approve_job(job_id):
    job = db.jobs.find_one({'_id': ObjectId(job_id)})
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    next_date = datetime.utcnow() + timedelta(days=30)
    db.jobs.update_one(
        {'_id': ObjectId(job_id)},
        {'$set': {'state': 'FIRST_EMAIL_SENT', 'last_sent_at': datetime.utcnow(), 'next_action_at': next_date}}
    )
    return jsonify({'status': 'Client email sent'}), 200

@app.route('/tasks/run', methods=['GET'])
def run_tasks():
    process_all_jobs()
    return jsonify({'status': 'Tasks executed'}), 200

# ───── NEW ROUTE: Send Email to Client ─────
@app.route('/send-email', methods=['GET'])
def send_email_to_client():
    job_id = request.args.get('job_id')
    if not job_id:
        return "Missing job_id", 400
    job = db.jobs.find_one({'_id': ObjectId(job_id)})
    if not job:
        return "Job not found", 404
    if not job.get("client_email") or not job.get("email_subject") or not job.get("email_body_html"):
        return "Missing email content", 400

    gmail_client.send_email(
        to_address=job["client_email"],
        subject=job["email_subject"],
        body=job["email_body_html"]
    )

    db.jobs.update_one({'_id': ObjectId(job_id)}, {'$set': {'state': 'EMAIL_SENT_TO_CLIENT'}})
    return "✅ Email sent to client"

# ───── NEW ROUTE: Edit Email (future use) ─────
@app.route('/edit-email', methods=['GET'])
def edit_email():
    job_id = request.args.get('job_id')
    return f"This is a placeholder for editing email with job_id {job_id}", 200

# ──────────────── Start App ────────────────
if __name__ == '__main__':
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5001,
        use_reloader=False
    )
