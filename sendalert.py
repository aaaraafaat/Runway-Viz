import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import sys

# Force UTF-8 for Windows (same fix as before)
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def send_email_alert(report_text, recipients):
    # ---------- CONFIGURE THESE ----------
    SENDER_EMAIL = "aaa.r.aa.f.aa.t@gmail.com"      # Replace with your Gmail
    APP_PASSWORD = "hhgk tjuv ttnw zneq" # Get from Google (see below)
    # --------------------------------------
    
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = "Runway Viz Weather Alert"
    msg.attach(MIMEText(report_text, 'plain', 'utf-8'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"[OK] Email sent to {len(recipients)} recipient(s)")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False

if __name__ == "__main__":
    # Read the latest report
    try:
        with open("latest_report.txt", "r", encoding='utf-8') as f:
            report = f.read()
    except FileNotFoundError:
        print("[ERROR] latest_report.txt not found. Run Runwayviz.py first.")
        sys.exit(1)
    
    # Send to yourself for testing
    send_email_alert(report, ["aaa.r.aa.f.aa.t@gmail.com"])  # Replace with your email