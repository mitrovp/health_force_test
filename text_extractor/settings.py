import os

from dotenv import load_dotenv

load_dotenv()

AWS_KEY_ID = os.getenv("AWS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
