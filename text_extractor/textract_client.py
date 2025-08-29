import boto3
from botocore.client import BaseClient

from text_extractor.settings import AWS_KEY_ID, AWS_SECRET_KEY


def get_textract_client() -> BaseClient:
    return boto3.client(
        "textract",
        aws_access_key_id=AWS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_KEY
    )
