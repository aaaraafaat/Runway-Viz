import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import sys

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def send_email_alert(report_text, recipients):
    sender_email = os.environ.get("GMAIL_USER")
    app_password = os.environ.get("GMAIL_APP_PASSWORD")
    
    if not sender_email or not app_password:
        print("[ERROR] Missing email credentials in environment")
        return False
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = "Runway Viz Weather Alert"
    msg.attach(MIMEText(report_text, 'plain', 'utf-8'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()
        print(f"[OK] Email sent to {len(recipients)} recipient(s)")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False

if __name__ == "__main__":
    try:
        with open("latest_report.txt", "r", encoding='utf-8') as f:
            report = f.read()
    except FileNotFoundError:
        print("[ERROR] latest_report.txt not found")
        sys.exit(1)
    
    # Replace with your email address(es)
    recipients = ["your_email@gmail.com"]
    send_email_alert(report, recipients)