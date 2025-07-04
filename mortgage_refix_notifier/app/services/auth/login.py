from flask import request
import hashlib
from pymongo import MongoClient
from app.config import Config

client = MongoClient(Config.MONGO_URI)
db = client["mortgage"]

def add_default_admin():
    # Default admin details
    default_admin_email = "smallbaby102@outlook.com"
    default_admin_password = "mortgageadmin"

    # Hash the password using SHA-256
    hashed_password = hashlib.sha256(default_admin_password.encode()).hexdigest()

    # Create the admin document
    admin_document = {
        'email': default_admin_email,
        'password': hashed_password
    }

    # Insert the document into the admin collection
    try:
        db.admin.insert_one(admin_document)
        print("Default admin account created successfully.")
    except Exception as e:
        print(f"Error inserting default admin: {e}")

def handle_admin_login():
    """
    Handles admin login authentication
    Returns:
        tuple: (dict response, int status_code)
    """
    email = request.form.get('email')
    code = request.form.get('code')

    if not email or not code:
        return {'error': 'Email and code are required'}, 400

    try:
        admin = db.admin.find_one({'email': email})

        if not admin:
            return {'error': 'Invalid credentials'}, 401

        stored_password_hash = admin["password"]
        input_password_hash = hashlib.sha256(code.encode()).hexdigest()

        # Check passcode
        
        if input_password_hash != stored_password_hash:
            return {'error': 'Incorrect passcode'}, 401

        return {
            'email': email
        }, 200

    except Exception as e:
        print(f"Login error: {e}")
        return {'error': 'Login failed'}, 500