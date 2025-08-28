import os
import re
import time
import traceback
from datetime import datetime

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    ElementHandle,
)

from post_extractor.app.constants import LOGIN_URL
from post_extractor.app.utils import (
    log_event,
    normalize_date,
    extract_hashtags,
    extract_links,
    random_delay,
    save_output,
)


async def extract_reactions_count(element: ElementHandle) -> int:
    reactions_count = 0
    try:
        if await element.query_selector(
            "span.social-details-social-counts__reactions-count"
        ):
            rc_text = await element.eval_on_selector(
                "span.social-details-social-counts__reactions-count",
                "el => el.innerText",
            )

            reactions_count = int(rc_text.replace(",", ""))
    except Exception as e:
        traceback.print_exception(e)

    return reactions_count


async def extract_comments_count(element: ElementHandle) -> int:
    comments_count = 0
    try:
        comments_li = await element.query_selector(
            "li.social-details-social-counts__comments"
        )
        if comments_li:
            span = await comments_li.query_selector("span")
            if span:
                cc_text = await span.inner_text()
                m = re.search(r"(\d+)", cc_text)
                if m:
                    comments_count = int(m.group(1))

    except Exception as e:
        traceback.print_exception(e)

    return comments_count


async def context_and_manual_login(
    session_file: str, browser: Browser
) -> BrowserContext:
    """
    Create a browser context, prompting for manual login if no session file exists.
    """
    if not os.path.exists(session_file) or os.stat(session_file).st_size == 0:
        log_event("SESSION_INIT", file=session_file)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()
        await page.goto(LOGIN_URL)
        print("Please log in manually, then press Enter here...")
        input()
        await context.storage_state(path=session_file)
        log_event("SESSION_SAVED", file=session_file)
    else:
        context = await browser.new_context(
            storage_state=session_file, viewport={"width": 1280, "height": 720}
        )

    return context


async def extract_date_text(element: ElementHandle) -> str:
    date_text = ""
    try:
        title_span = await element.query_selector(
            "span.update-components-actor__sub-description"
        )
        if title_span:
            date_text_span = await title_span.query_selector("span[aria-hidden='true']")
            if date_text_span:
                date_text = await date_text_span.inner_text()

    except Exception as e:
        traceback.print_exception(e)

    return date_text


async def extract_author_name(element: ElementHandle) -> str:
    name = ""
    try:
        title_span = await element.query_selector("span.update-components-actor__title")
        if title_span:
            name_span = await title_span.query_selector("span[aria-hidden='true']")
            if name_span:
                name = await name_span.inner_text()

    except Exception as e:
        traceback.print_exception(e)

    return name


async def extract_post_id(element: ElementHandle) -> int:
    raw_post_id = await element.get_attribute("data-urn")
    post_id = int(raw_post_id.split(":")[-1]) if raw_post_id else 0
    return post_id


async def process_posts(posts: list[ElementHandle]) -> list[dict]:
    """Process a list of post elements and extract structured data from each."""
    results = []
    for idx, post in enumerate(posts):
        try:
            post_id = idx
            post_author = await extract_author_name(post)
            date_text = await extract_date_text(post)
            posted_at = normalize_date(date_text)

            text = ""
            element = await post.query_selector("div.feed-shared-update-v2")
            if element:
                text = await post.eval_on_selector(
                    "div.feed-shared-update-v2__description", "el => el.innerText"
                )
                post_id = await extract_post_id(element)

            hashtags = extract_hashtags(text)
            links = extract_links(text)

            reactions_count = await extract_reactions_count(post)

            comments_count = await extract_comments_count(post)

            results.append(
                {
                    "post_id": post_id,
                    "author_name": post_author,
                    "posted_at": posted_at,
                    "text": text,
                    "hashtags": hashtags,
                    "links": links,
                    "reactions_count": reactions_count,
                    "comments_count": comments_count,
                }
            )
            log_event("POST_LOADED", post_id=post_id, idx=idx)

            await random_delay()

        except Exception as e:
            log_event("WARN_EXTRACTION_ERROR", error=str(e))

    return results


async def scrape(profile_url: str, session_file: str, min_posts: int = 10) -> None:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await context_and_manual_login(session_file, browser)
        page = await context.new_page()

        log_event("NAV_PROFILE", url=profile_url)
        await page.goto(profile_url)
        await random_delay()

        await page.click("a[href*='recent-activity']")
        await random_delay()
        log_event("NAV_POSTS_TAB")
        await random_delay()

        start = time.time()

        post_selector = ".AyAfzTZBQSDwpiHasRnjtXFsKCJXamNffNgk"
        posts = []
        while True:
            posts = await page.query_selector_all(post_selector)

            for post in posts:
                await post.scroll_into_view_if_needed()
                await random_delay(800, 1500)

            if len(posts) >= min_posts or (time.time() - start) > 60:
                break

            await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            await random_delay(1200, 2500)

            log_event("SCROLL_MORE", current_posts=len(posts))

        results = await process_posts(posts)

        posts_count = len(results)
        out = {
            "profile_url": profile_url,
            "fetched_at": datetime.now().isoformat() + "Z",
            "total_posts": posts_count,
            "posts": results,
        }
        save_output(out, posts_count)

        await browser.close()
