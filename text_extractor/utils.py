import json
from datetime import datetime

from text_extractor.paths import LOG_PATH


def read_file(file_path: str) -> bytes:
    """Reads an image or pdf from the specified file path.
    """
    with open(file_path, "rb") as document:
        image_bytes = document.read()
    return image_bytes


def log_event(event: str, **kwargs) -> None:
    entry = {"event": event, "ts": datetime.now().isoformat() + "Z", **kwargs}
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def save_output(data: dict, file_path: str) -> None:
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log_event("OUTPUT_SAVED")
