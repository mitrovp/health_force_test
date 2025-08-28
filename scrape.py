import asyncio
import argparse

from post_extractor.app.constants import STORAGE_STATE_PATH, PROFILE_URL
from post_extractor.app.scraper import scrape

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("profile_url", default=PROFILE_URL)
    ap.add_argument("--min-posts", type=int, default=10)
    ap.add_argument("--session", default=STORAGE_STATE_PATH)
    args = ap.parse_args()

    asyncio.run(scrape(args.profile_url, args.session, args.min_posts))
