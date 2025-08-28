import asyncio
import json
import random
import re
from datetime import datetime, timezone, timedelta


from post_extractor.app.constants import LOG_PATH, OUTPUT_JSON_PATH


async def random_delay(min_ms: int = 100, max_ms: int = 400) -> None:
    delay = random.uniform(min_ms / 1000, max_ms / 1000)
    await asyncio.sleep(delay)


def log_event(event: str, **kwargs) -> None:
    entry = {"event": event, "ts": datetime.now().isoformat() + "Z", **kwargs}
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def save_output(data: dict, post_count: int) -> None:
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log_event("OUTPUT_SAVED", total=post_count)


def extract_hashtags(text: str) -> list[str]:
    return re.findall(r"#\w+", text) if text else []


def extract_links(text: str) -> list[str]:
    url_pattern = r"https?://[^\s]+"
    return re.findall(url_pattern, text)


def normalize_date(text: str) -> str | None:
    """
    Convert LinkedIn relative timestamps (e.g., "2h ago", "3 days ago") to ISO-8601.
    """
    if not text:
        return None

    text = text.lower()
    now = datetime.now(timezone.utc)

    try:
        if "h" in text:
            hours = int(re.search(r"(\d+)\s*h", text).group(1))
            return (now - timedelta(hours=hours)).isoformat()
        elif "mo" in text:
            months = int(re.search(r"(\d+)\s*mo", text).group(1))
            return (now - timedelta(days=30 * months)).isoformat()
        elif "m" in text:
            minutes = int(re.search(r"(\d+)\s*m", text).group(1))
            return (now - timedelta(minutes=minutes)).isoformat()
        elif "d" in text:
            days = int(re.search(r"(\d+)\s*d", text).group(1))
            return (now - timedelta(days=days)).isoformat()
        elif "w" in text:
            weeks = int(re.search(r"(\d+)\s*w", text).group(1))
            return (now - timedelta(weeks=weeks)).isoformat()
        elif "yr" in text:
            years = int(re.search(r"(\d+)\s*yr", text).group(1))
            return (now - timedelta(days=365 * years)).isoformat()
        else:
            return datetime.strptime(text, "%b %d, %Y").replace(tzinfo=timezone.utc).isoformat()
    except Exception as e:
        log_event("WARN_DATE_PARSE_FAIL", raw=text, error=str(e))
        return None
