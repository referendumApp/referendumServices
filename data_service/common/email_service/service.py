import os
import logging
import base64
from pathlib import Path
from pydantic import EmailStr
from datetime import datetime

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.message import EmailMessage
from jinja2 import Environment, FileSystemLoader

from api.settings import settings

from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        # Load Gmail API credentials
        self.credentials = service_account.Credentials.from_service_account_info(
            {
                "type": "service_account",
                "project_id": os.getenv("GMAIL_PROJECT_ID"),
                "private_key": os.getenv("GMAIL_PRIVATE_KEY"),
                "client_email": os.getenv("GMAIL_CLIENT_EMAIL"),
                "token_uri": os.getenv("GMAIL_TOKEN_URI"),
                "auth_uri": os.getenv("GMAIL_AUTH_URI"),
            },
            scopes=["https://www.googleapis.com/auth/gmail.send"],
            subject=os.getenv("GMAIL_SERVICE_USER", "admin@referendumapp.com"),
        )
        # Create Gmail API service
        self.service = build('gmail', 'v1', credentials=self.credentials)
        self.sender = os.getenv("GMAIL_SERVICE_USER", "admin@referendumapp.com")
        self.templates_dir = os.path.join(Path(__file__).parent.absolute(), "templates")
        self.env = Environment(loader=FileSystemLoader(self.templates_dir))


    async def send_password_reset_token_email(self, to_email: EmailStr, subject: str, username: str, passcode: str):
        try:
            template = self.env.get_template("password_reset.html")
            html_content = template.render(
                passcode=passcode,
                token_expiry=settings.RESET_TOKEN_EXPIRE_MINUTES,
                username=username,
                year=datetime.now().year
            )
            message = MIMEMultipart('alternative')
            message['To'] = to_email
            message['From'] = self.sender
            message['Subject'] = subject

            html_part = MIMEText(html_content, 'html')
            message.attach(html_part)

            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            create_message = {"raw": encoded_message}
            send_message = (
                self.service.users()
                .messages()
                .send(userId=os.getenv("GMAIL_SERVICE_USER", "admin@referendumapp.com"), body=create_message)
                .execute()
            )
            logger.info(f"Message sent to {to_email}")
        except HttpError as e:
            logger.error(f"An error has occurred: {e}")

email_service = EmailService()

def get_email_service():
    return email_service
