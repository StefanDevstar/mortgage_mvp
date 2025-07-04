from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, flash, render_template_string

# Imports from your existing services
from app.services.auth.login import add_default_admin, handle_admin_login
from app.services.dashboard import getMetrics, saveLog

from bson.objectid import ObjectId
from app import gmail_client
from app.config import Config
from pymongo import MongoClient
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)
client = MongoClient(Config.MONGO_URI)
db = client["mortgage"]

@admin_bp.route('/add_default_admin')
def addDefaultAdmin():
    add_default_admin()
    return redirect(url_for('admin.adminLogin'))

 

@admin_bp.route('/admin')
def admins():
    """
    Render the main admin dashboard.
    """
    if 'admin_email' not in session:
        return redirect(url_for('admin.adminLogin'))

    return render_template(
        'admin_page.html',
         metrics = getMetrics()
    )


@admin_bp.route('/admin-login')
def adminLogin():
    """
    Show admin login form (GET).
    """
    return render_template('adminlogin.html')


@admin_bp.route('/admin-login', methods=['POST'])
def admin_login():
    """
    Handle admin login (POST).
    """
    result, status_code = handle_admin_login()
    if status_code != 200:
        return render_template('adminlogin.html', error=result.get('error', 'Unknown error')), status_code

    session['admin_email'] = result['email']
    return redirect(url_for('admin.admins'))


@admin_bp.route('/admin-logout')
def admin_logout():
    """
    Clear admin session and redirect to login.
    """
    session.clear()
    return jsonify({'redirect_url': url_for('admin.adminLogin')})


# /* *************** API for Metrics **************/
@admin_bp.route('/metrics')
def get_metrics():
    metrics = getMetrics()
    return jsonify({'metrics': metrics})
 

 
# 🔷 HTML form for editing (textarea uses safe rendering)
EDIT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Edit Email</title>
</head>
<body>
    <h2>Edit Email for {{ customer }}</h2>
    <form method="POST">
        <label>To:</label><br>
        <input type="email" name="to" value="{{ to }}" required style="width:100%"><br><br>

        <label>Subject:</label><br>
        <input type="text" name="subject" value="{{ subject }}" required style="width:100%"><br><br>

        <label>Body (HTML Supported):</label><br>
        <textarea name="body" rows="20" style="width:100%;">{{ body|safe }}</textarea><br><br>

        <button type="submit">✅ Send to Client</button>
    </form>
</body>
</html>
"""

# 🔷 Route: Edit email page
@admin_bp.route("/edit-email", methods=["GET", "POST"])
def edit_email():
    job_id = request.args.get("job_id")
    job = db.jobs.find_one({"_id": ObjectId(job_id)})

    if not job:
        flash("Job not found.", "danger")
        return "Job not found"

    if request.method == "POST":
        to = request.form.get("to")
        subject = request.form.get("subject")
        body = request.form.get("body").replace('\n', '<br>')

        try:
            # ✅ Send updated HTML email to client
            gmail_client.send_email(
                to_address=to,
                subject=subject,
                body=body,
                job_id=job_id,
                is_html=True,
                is_client_email=True
            )
            
            new_state = "FIRST_EMAIL_SENT" if job.get('state') == "AWAITING_BROKER_REVIEW" else "SECOND_EMAIL_SENT"

            # ✅ Update DB with clean HTML
            db.jobs.update_one({"_id": ObjectId(job_id)}, {
                "$set": {
                    "state": new_state,
                    "email_subject": subject,
                    "email_body_html": body,
                    "last_sent_at": datetime.utcnow(),
                    "next_action_at": datetime.utcnow() + timedelta(days=30)
                }
            })

            flash("✅ Updated and sent to client.", "success")
            return "✅ Updated and sent to client."
        except Exception as e:
            print(f"⚠️ Failed to send edited email: {e}")
            saveLog("Send edited email", e)
            flash("An error occurred while sending the edited email.", "danger")

        return "An error occurred while sending the edited email."

    # 👇 Render form with current HTML content (escaped)
    return render_template_string(EDIT_TEMPLATE,
        to=job.get("client_email", ""),
        subject=job.get("email_subject", ""),
        body=job.get("email_body_html", ""),
        customer=job.get("Customer", "Client")
    )


# 🔷 Route: Send saved version of client email
@admin_bp.route("/send-email", methods=["GET"])
def send_email_to_client():
    job_id = request.args.get("job_id")
    job = db.jobs.find_one({"_id": ObjectId(job_id)})

    if not job:
        flash("Job not found.", "danger")
        return "Job not found."
    
    client_email = job.get("client_email")
    subject = job.get("email_subject")
    html_body = job.get("email_body_html").replace('\n', '<br>')
    if not client_email or not subject or not html_body:
        flash("Missing email fields in DB.", "warning")
        saveLog("Send email", "Missing email fields in DB.")
        return "Missing email fields in DB.", "warning"

    try:
        gmail_client.send_email(
            to_address=client_email,
            subject=subject,
            body=html_body,
            job_id=job_id,
            is_html=True,
            is_client_email=True
        )

        new_state = "FIRST_EMAIL_SENT" if job.get('state') == "AWAITING_BROKER_REVIEW" else "SECOND_EMAIL_SENT"

        db.jobs.update_one({"_id": ObjectId(job_id)}, {
            "$set": {
                "state": new_state,
                "last_sent_at": datetime.utcnow(),
                "next_action_at": datetime.utcnow() + timedelta(days=30)
            }
        })

        flash("✅ Email sent to client.", "success")
        return "Email sent to client."

    except Exception as e:
        print(f"⚠️ Error sending email: {e}")
        saveLog("Send email", e)
        
        flash("An error occurred while sending email.", "danger")

    return "An error occurred while sending email."
