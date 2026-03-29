import boto3
from app.core.config import settings

ses_client = boto3.client("ses", region_name="ap-south-1", aws_access_key_id=settings.AWS_ACCESS_KEY, aws_secret_access_key=settings.AWS_SECRET_KEY)

def send_email(to_address: str, subject: str, body: str, is_html: bool = False):
    message_body = {"Html": {"Data": body, "Charset": "UTF-8"}} if is_html else {"Text": {"Data": body, "Charset": "UTF-8"}}

    ses_client.send_email(
        Source=settings.ADMIN_EMAIL,  # Must be verified in SES
        Destination={"ToAddresses": [to_address]},
        Message={
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": message_body
        }
    )