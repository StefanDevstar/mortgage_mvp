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

@app.route('/run', methods=['GET'])
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