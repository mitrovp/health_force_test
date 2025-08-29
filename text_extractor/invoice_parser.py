import re

from botocore.client import BaseClient

from text_extractor.paths import INVOICE_JSON_PATH
from text_extractor.text_extractor import call_textract_multiple_pages
from text_extractor.utils import save_output, log_event


def get_text_for_block(block, block_map):
    """Collect all text from child WORD/LINE blocks of a given block."""
    text = []
    if "Relationships" in block:
        for rel in block["Relationships"]:
            if rel["Type"] == "CHILD":
                for child_id in rel["Ids"]:
                    child = block_map[child_id]
                    if child["BlockType"] in ["WORD", "LINE"]:
                        text.append(child["Text"])
    return " ".join(text).strip()


def extract_key_value_pairs(textract_resp):
    blocks = textract_resp["Blocks"]
    block_map = {b["Id"]: b for b in blocks}

    kvs = {}
    for block in blocks:
        if block["BlockType"] == "KEY_VALUE_SET" and "KEY" in block.get(
            "EntityTypes", []
        ):
            key_text = get_text_for_block(block, block_map)

            value_block = None
            for rel in block.get("Relationships", []):
                if rel["Type"] == "VALUE":
                    for vid in rel["Ids"]:
                        value_block = block_map[vid]
                        value_text = get_text_for_block(value_block, block_map)
                        kvs[key_text] = value_text
    return kvs


def normalize_invoice_fields(kvs):
    result = {
        "invoice_number": kvs.get("NUMERO DOCUMENTO") or kvs.get("No."),
        "issue_date": kvs.get("DATA DOCUMENTO") or kvs.get("DATA"),
        "due_date": kvs.get("DATA"),
        "supplier_name": kvs.get("Supplier") or kvs.get("Vendor"),
        "invoice_total": kvs.get("TOTALE DOCUMENTO"),
        "currency": None,
    }

    if result["invoice_total"]:
        if "€" in result["invoice_total"]:
            result["currency"] = "EUR"
        elif "$" in result["invoice_total"]:
            result["currency"] = "USD"
    return result


def extract_tables(textract_resp):
    blocks = textract_resp["Blocks"]
    block_map = {b["Id"]: b for b in blocks}

    tables = []
    for block in blocks:
        if block["BlockType"] == "TABLE":
            table = []
            cells = [
                block_map[rel_id]
                for rel in block.get("Relationships", [])
                if rel["Type"] == "CHILD"
                for rel_id in rel["Ids"]
            ]

            for cell in cells:
                if cell["BlockType"] == "CELL":
                    text = get_text_for_block(cell, block_map)
                    row, col = cell.get("RowIndex"), cell.get("ColumnIndex")
                    cell_type = cell.get("EntityTypes", [])
                    table.append(
                        {
                            "row": row,
                            "col": col,
                            "text": text,
                            "type": cell_type[0] if cell_type else None,
                        }
                    )
            tables.append(table)
    return tables


def normalize_table(table):
    headers = {}
    for cell in table:
        if cell.get("type") == "COLUMN_HEADER" or cell["row"] == 1:
            headers[cell["col"]] = cell["text"]

    rows = []
    for cell in table:
        if cell.get("type") == "COLUMN_HEADER":
            continue
        row_idx = cell["row"]
        if row_idx not in [r.get("row") for r in rows]:
            rows.append({"row": row_idx})
        for r in rows:
            if r["row"] == row_idx:
                col_name = headers.get(cell["col"], f"col{cell['col']}")
                r[col_name] = cell["text"]

    return [{k: v for k, v in r.items() if k != "row"} for r in rows]


def parse_line_items(tables):
    """
    Parse extracted Textract tables into normalized line items.
    Args:
        tables: list of tables (each table = list of dicts with column headers as keys)
    Returns:
        list of dicts: [{description, qty, unit_price, total}, ...]
    """
    line_items = []

    if not tables:
        return line_items

    for row in tables[0]:
        desc = row.get("DESCRIZIONE", "").strip()
        qty = row.get("QUANTITA'", "").strip()

        unit_price, total = None, None
        for val in row.values():
            if not val:
                continue
            val_norm = val.replace(",", ".")

            money_match = re.findall(r"\d+(\.\d{1,2})?", val_norm)
            if money_match:
                num = val_norm
                if not unit_price:
                    unit_price = num
                else:
                    total = num

        if not qty and desc:
            qty = "1"

        if desc and len(desc) > 2:
            line_items.append(
                {
                    "description": desc,
                    "quantity": qty,
                    "unit_price": unit_price,
                    "total": total,
                }
            )
    log_event("LINE_ITEMS_EXTRACTED", count=len(line_items))
    return line_items


def parse_invoice(file_path: str, textract_client: BaseClient):
    log_event("INVOICE_PARSING_STARTED", file_path=file_path)
    try:
        invoice_data = call_textract_multiple_pages(
            textract_client, file_path, page_count=2
        )

        tables_all = []
        key_values_all = {}
        for i, page in enumerate(invoice_data):
            log_event("PAGE_PROCESSING", page_number=i + 1)

            key_value_page = extract_key_value_pairs(page)
            key_values_all.update(key_value_page)

            tables = extract_tables(page)
            tables_all.extend(tables)

        tables_all = [normalize_table(t) for t in tables_all]

        result = normalize_invoice_fields(key_values_all)
        line_items = parse_line_items(tables_all)
        result["line_items"] = line_items

        save_output(result, INVOICE_JSON_PATH)

    except Exception as e:
        log_event("INVOICE_PARSING_FAILED", file_path=file_path, error=str(e))
        raise
