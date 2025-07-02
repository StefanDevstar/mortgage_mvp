import os
from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from app.config import Config
from app.tasks import process_all_jobs
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

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

def start_scheduler():
    print("***********Started Scheduler************")
    scheduler = BackgroundScheduler()
    # Run every day at 02:00 AM
    scheduler.add_job(
        func=process_all_jobs,
        trigger=CronTrigger(hour=2, minute=0),
        # trigger=CronTrigger(minute="*"),
        id="daily_refix_job",
        replace_existing=True
    )
    scheduler.start()

# Kick off the scheduler when Flask starts
with app.app_context():
    start_scheduler()


from app.routes.admin_routes import admin_bp

app.register_blueprint(admin_bp)


@app.route('/', methods=['GET'])
def root():
    return jsonify({'status': 'Tasks executed'}), 200


# Endpoint to create a new refix job
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

# Endpoint for broker approval (send to client)
@app.route('/jobs/<job_id>/approve', methods=['POST'])
def approve_job(job_id):
    job = db.jobs.find_one({'_id': ObjectId(job_id)})
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    # Send client email and schedule follow-up
    # send_client_email(job)
    next_date = datetime.utcnow() + timedelta(days=30)
    db.jobs.update_one(
        {'_id': ObjectId(job_id)},
        {'$set': {'state': 'FIRST_EMAIL_SENT', 'last_sent_at': datetime.utcnow(), 'next_action_at': next_date}}
    )
    return jsonify({'status': 'Client email sent'}), 200

# Webhook or manual trigger to retry tasks
@app.route('/tasks/run', methods=['GET'])
def run_tasks():
    process_all_jobs()
    return jsonify({'status': 'Tasks executed'}), 200

if __name__ == '__main__':
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5001,
        use_reloader=False
    )