from text_extractor.invoice_parser import parse_invoice
from text_extractor.paths import INVOICE_FILE_PATH
from text_extractor.textract_client import get_textract_client

if __name__ == "__main__":
    textract_client = get_textract_client()
    parse_invoice(INVOICE_FILE_PATH, textract_client)
