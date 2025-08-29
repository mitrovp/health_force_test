# LinkedIn Post Extractor

This Python application scrapes posts from a LinkedIn profile using Playwright for browser automation.

## Installation

1. Clone the repository or download the source code.

2. Install dependencies:

**pip install -r requirements.txt**

3. Install Playwright browsers:

**playwright install**

## Usage

Run the scraper with your desired LinkedIn profile URL:

**python main.py PROFILE_URL [--min-posts MIN_POSTS] [--session PATH_TO_SESSION_FILE]**

Default values: 
MIN_POSTS = 10, 
PATH_TO_SESSION_FILE = 'post_extractor/out/li_storage_state.json'

- `PROFILE_URL`: The LinkedIn profile URL to scrape posts from.
- `--min-posts`: Minimum number of posts to fetch (default: 10).
- `--session`: Path to Playwright storage state file for authentication (default: path defined in `STORAGE_STATE_PATH`).

Example:

**python scrape.py https://www.linkedin.com/in/example-profile --min-posts 20 --session post_extractor/out/li_storage_state.json**

or just **python scrape.py https://www.linkedin.com/in/example-profile** to use default values.

## Notes

- The scraper runs with a visible browser window by default for debugging (`headless=False`).
- First signing in to LinkedIn will be manual, then will be saved the session state for authenticated scraping.
---

This will get you started with scraping LinkedIn posts using the provided scraper code.



# Invoice Parser

This project provides a Python script to parse invoice documents using AWS Textract. It extracts key-value pairs and tables across multiple pages, normalizes the data, and outputs structured invoice information including line items.

## Key Features

- Processes multi-page invoices (example set to 2 pages)
- Extracts key-value pairs and tabular data from each page
- Normalizes extracted tables and invoice fields
- Combines all data into a consolidated JSON output
- Logs key events for tracking parsing progress and errors

## Usage

1. Install dependencies: **pip install -r requirements.txt**
2. Ensure AWS credentials and permissions for Textract are set up.
3. Place the invoice file path in `INVOICE_FILE_PATH`.
4. Run the parser: **python extract.py**
5. The parsed invoice data will be saved to `OUTPUT_FILE_PATH` in JSON format.
