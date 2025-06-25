from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from config import Config
import tasks

app = Flask(__name__)
app.config.from_object(Config)
mongo = PyMongo(app)

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
    result = mongo.db.jobs.insert_one(job)
    return jsonify({'job_id': str(result.inserted_id)}), 201

# Endpoint for broker approval (send to client)
@app.route('/jobs/<job_id>/approve', methods=['POST'])
def approve_job(job_id):
    job = mongo.db.jobs.find_one({'_id': ObjectId(job_id)})
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    # Send client email and schedule follow-up
    tasks.send_client_email(job)
    next_date = datetime.utcnow() + timedelta(days=30)
    mongo.db.jobs.update_one(
        {'_id': ObjectId(job_id)},
        {'$set': {'state': 'FIRST_EMAIL_SENT', 'last_sent_at': datetime.utcnow(), 'next_action_at': next_date}}
    )
    return jsonify({'status': 'Client email sent'}), 200

# Webhook or manual trigger to retry tasks
@app.route('/tasks/run', methods=['POST'])
def run_tasks():
    tasks.process_all_jobs()
    return jsonify({'status': 'Tasks executed'}), 200

if __name__ == '__main__':
    app.run(debug=True)