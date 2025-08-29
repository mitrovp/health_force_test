import logging
import time

from botocore.client import BaseClient

from text_extractor.utils import read_file


def call_textract(client: BaseClient, file_path: str, retries: int = 3, backoff: int = 2) -> dict:
    image_bytes = read_file(file_path)
    features = ["TABLES", "FORMS"]
    attempt = 0
    while attempt <= retries:
        try:
            resp = client.analyze_document(
                Document={"Bytes": image_bytes},
                FeatureTypes=features
            )
            return resp
        except Exception as e:
            logging.error(f"Textract attempt {attempt} failed: {e}")
            if attempt == retries:
                raise
            time.sleep(backoff * (2 ** attempt))
            attempt += 1


def call_textract_multiple_pages(client: BaseClient, file_path: str, page_count: int) -> list[dict]:
    responses = []
    for i in range(1, page_count + 1):
        response = call_textract(client, file_path.format(i=i))
        responses.append(response)
    return responses
