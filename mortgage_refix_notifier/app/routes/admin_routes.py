from flask import Blueprint, redirect, url_for, flash, request, render_template_string
from bson.objectid import ObjectId
from app import gmail_client
from app.config import Config
from pymongo import MongoClient
from datetime import datetime, timedelta
import html

# 🔷 Blueprint setup
admin_bp = Blueprint("admin", __name__)
client = MongoClient(Config.MONGO_URI)
db = client["mortgage"]

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
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        to = request.form.get("to")
        subject = request.form.get("subject")
        body = request.form.get("body")

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

            # ✅ Update DB with clean HTML
            db.jobs.update_one({"_id": ObjectId(job_id)}, {
                "$set": {
                    "state": "FIRST_EMAIL_SENT",
                    "email_subject": subject,
                    "email_body_html": body,
                    "last_sent_at": datetime.utcnow(),
                    "next_action_at": datetime.utcnow() + timedelta(days=30)
                }
            })

            flash("✅ Updated and sent to client.", "success")
        except Exception as e:
            print(f"⚠️ Failed to send edited email: {e}")
            flash("An error occurred while sending the edited email.", "danger")

        return redirect(url_for("dashboard.index"))

    # 👇 Render form with current HTML content (escaped)
    return render_template_string(EDIT_TEMPLATE,
        to=job.get("client_email", ""),
        subject=job.get("email_subject", ""),
        body=job.get("email_body_html", ""),
        customer=job.get("Customer", "Client")
    )


# 🔷 Route: Send saved version of client email
@admin_bp.route("/send-email/<job_id>", methods=["GET"])
def send_email_to_client(job_id):
    job = db.jobs.find_one({"_id": ObjectId(job_id)})

    if not job:
        flash("Job not found.", "danger")
        return redirect(url_for("dashboard.index"))

    client_email = job.get("client_email")
    subject = job.get("email_subject")
    html_body = job.get("email_body_html")

    if not client_email or not subject or not html_body:
        flash("Missing email fields in DB.", "warning")
        return redirect(url_for("dashboard.index"))

    try:
        gmail_client.send_email(
            to_address=client_email,
            subject=subject,
            body=html_body,
            job_id=job_id,
            is_html=True,
            is_client_email=True
        )

        db.jobs.update_one({"_id": ObjectId(job_id)}, {
            "$set": {
                "state": "FIRST_EMAIL_SENT",
                "last_sent_at": datetime.utcnow(),
                "next_action_at": datetime.utcnow() + timedelta(days=30)
            }
        })

        flash("✅ Email sent to client.", "success")

    except Exception as e:
        print(f"⚠️ Error sending email: {e}")
        flash("An error occurred while sending email.", "danger")

    return redirect(url_for("dashboard.index"))
