import logging
import requests
import markdown
from xhtml2pdf import pisa
from io import BytesIO
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from utils.config import (
    ENABLE_NOTIFICATIONS,
    PUSHOVER_USER_KEY,
    PUSHOVER_API_TOKEN,
    SENDGRID_API_KEY,
    SENDER_EMAIL,
    RECIPIENT_EMAIL
)

logger = logging.getLogger(__name__)

def send_push_notification(message: str) -> bool:
    """Sends a push notification via Pushover."""
    if not ENABLE_NOTIFICATIONS or not PUSHOVER_USER_KEY or not PUSHOVER_API_TOKEN:
        logger.info(f"[MOCK] Push Notification: {message}")
        return False
    
    try:
        url = "https://api.pushover.net/1/messages.json"
        data = {
            "token": PUSHOVER_API_TOKEN,
            "user": PUSHOVER_USER_KEY,
            "message": message
        }
        res = requests.post(url, data=data, timeout=10)
        res.raise_for_status()
        logger.info("✅ Push notification sent successfully.")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send push notification: {e}")
        return False

def generate_pdf_from_markdown(report: str) -> bytes:
    html_content = markdown.markdown(report, extensions=['tables', 'fenced_code', 'nl2br'])
    styled_html = f"""
    <html>
    <head>
    <style>
        body {{ font-family: Helvetica, Arial, sans-serif; font-size: 11pt; line-height: 1.5; color: #000000; }}
        h1 {{ color: #000000; font-size: 18pt; }}
        h2 {{ color: #000000; font-size: 14pt; margin-top: 15px; }}
        p, li, span {{ color: #000000; }}
        a {{ color: #000000; text-decoration: underline; }}
        p {{ margin-bottom: 10px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; color: #000000; }}
        th {{ background-color: #f2f2f2; }}
    </style>
    </head>
    <body>
    {html_content}
    </body>
    </html>
    """
    result_file = BytesIO()
    pisa_status = pisa.CreatePDF(styled_html, dest=result_file)
    if pisa_status.err:
        raise Exception("Failed to generate PDF")
    return result_file.getvalue()

def send_email_report(topic: str, report: str, recipient_email: str = None) -> bool:
    """Sends the full research report as a PDF via SendGrid."""
    target_email = recipient_email or RECIPIENT_EMAIL
    if not ENABLE_NOTIFICATIONS or not SENDGRID_API_KEY or not SENDER_EMAIL or not target_email:
        logger.info(f"[MOCK] Email Report for {topic} sent to console.")
        print(f"\n--- MOCK EMAIL START ---\nTo: {target_email}\nSubject: Research Report: {topic}\n\n[PDF Attachment generated from report]\n--- MOCK EMAIL END ---\n")
        return False

    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=target_email,
        subject=f"Research Report: {topic}",
        plain_text_content="Please find the attached PDF report for your research.",
        html_content="<p>Please find the attached PDF report for your research.</p>"
    )
    
    try:
        pdf_bytes = generate_pdf_from_markdown(report)
        encoded_file = base64.b64encode(pdf_bytes).decode()
        
        attachment = Attachment()
        attachment.file_content = FileContent(encoded_file)
        attachment.file_type = FileType('application/pdf')
        safe_topic = topic.replace(' ', '_').replace('/', '_')
        attachment.file_name = FileName(f"{safe_topic}_Report.pdf")
        attachment.disposition = Disposition('attachment')
        
        message.attachment = attachment
    except Exception as e:
        logger.error(f"Failed to attach PDF, falling back to text: {e}")
        message.plain_text_content = report
    
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(f"✅ Email report sent successfully (Status: {response.status_code}).")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send email report: {e}")
        return False
