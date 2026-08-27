# FlyRank A9 — The Polite Scraper

## Target Classification

### Target

**Books to Scrape**

https://books.toscrape.com/

Books to Scrape is a public practice sandbox specifically designed for learning and testing web scraping technologies. This assignment uses it because it is intended for scraping practice.

### Scope

This scraper processes **only the first three catalogue pages** and discovers the **60 books** listed on those pages.

For each book, the scraper collects:

* `title`
* `product_url`
* `price_text`
* `availability_text`
* `rating_text`
* `description`
* `source_page`
* `fetched_at`

The cleaned records also contain:

* `price_gbp`

### Robots Check

I requested:

https://books.toscrape.com/robots.txt

The response was **HTTP 404 Not Found**, so no robots file was found.

A missing robots file is not treated as permission to scrape other websites.

This assignment uses Books to Scrape because it is explicitly provided as a public practice scraping sandbox.

### Responsible Scraping

The scraper uses an identifying User-Agent, a request timeout, caching, and at least 500 ms between real requests.

During development, cached HTML is used instead of repeatedly requesting the website.

**I will not reuse this code on another site without checking its rules and terms first.**

---

## Technology

This project uses the **Python lane**.

* Python 3.10+
* `requests` for HTTP requests
* `BeautifulSoup` for HTML parsing
* `Pydantic` for schema validation
* Python `json` module for JSON output

The project does not require a browser or JavaScript automation.

---

## Installation

From the `scraper` directory, install the required Python dependencies:

```powershell
pip install requests beautifulsoup4 pydantic
```

The scraper has no database, paid service, proxy, or API key requirement.

---

## Running the Scraper

From the `scraper` directory, run:

```powershell
python src/main.py
```

The scraper produces:

```text
output/books.json
output/errors.json
output/run-report.json
```

Cached HTML is stored under:

```text
cache/
```

The cache directory should not be committed to GitHub.

---

## Scraping and Politeness Rules

The scraper follows these rules:

* **User-Agent:** `PoliteScraper/1.0`
* **Delay:** at least `0.5` seconds between real requests
* **Timeout:** `10` seconds
* **HTTP status:** the response status is checked before parsing
* **Caching:** catalogue and detail HTML pages are cached locally
* **Development:** cached pages are reused instead of repeatedly requesting the website
* **Retries:** a timeout or HTTP 5xx error is retried once
* **403 and 404:** these are not retried
* **Scope:** only the first three catalogue pages are processed
* **Duplicates:** duplicate product URLs are removed

Cached pages do not make network requests, so they do not require the request delay.

---

## Catalogue Discovery

The scraper starts from:

```text
https://books.toscrape.com/catalogue/page-1.html
```

It parses each catalogue page with Beautiful Soup, extracts book links, and converts relative URLs into absolute URLs using Python's `urljoin()`.

The catalogue's own `next` link is followed to discover pages 2 and 3.

The scraper does not hardcode the 60 individual book URLs.

Expected discovery result:

```text
catalogue_pages=3
discovered=60
unique_urls=60
```

---

## Record Schema

Each valid record has the following structure:

```json
{
  "title": "A Light in the Attic",
  "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "price_text": "£51.77",
  "price_gbp": 51.77,
  "availability_text": "In stock (22 available)",
  "rating_text": "Three",
  "description": "...",
  "source_page": "https://books.toscrape.com/catalogue/page-1.html",
  "fetched_at": "2026-08-27T17:00:00+00:00"
}
```

The Pydantic model validates the following types:

```text
title: str
product_url: HttpUrl
price_text: str
price_gbp: float
availability_text: str
rating_text: str
description: str | None
source_page: HttpUrl
fetched_at: str
```

The original `price_text` is preserved as scraped, while `price_gbp` is normalized to a numeric value.

Missing descriptions are stored as `null`. The scraper does not invent missing data.

---

## Extraction and Validation

The scraper visits all 60 discovered book pages and extracts the required raw fields from the product area of each page.

Each record is normalized before storage.

For example:

```text
"£51.77" → 51.77
```

Every record is then validated with Pydantic.

If a record fails validation or a page cannot be processed, it is not added to `books.json`.

Failed pages are recorded in:

```text
output/errors.json
```

with the failed URL and the reason for the failure.

---

## Output

### `output/books.json`

Contains the validated records.

A successful clean run contains exactly:

```text
60 records
```

Duplicate records are not stored.

Running the scraper again does not append another copy of the same 60 records.

### `output/errors.json`

Contains failed pages and their reasons.

The Stage 5 test deliberately adds one fake URL to verify that a broken page does not stop the scraper.

### `output/run-report.json`

Contains:

* `start_time`
* `duration_seconds`
* `pages_fetched`
* `cache_hits`
* `valid_records`
* `invalid_records`
* `failed_pages`

---

## Stage 5 Failure Test

A deliberately fake URL was added to the scraper:

```text
https://books.toscrape.com/catalogue/this-page-does-not-exist_999999/index.html
```

The scraper handled the 404 without crashing.

The resulting run report was:

```json
{
  "start_time": "2026-08-27T17:13:12.398557+00:00",
  "duration_seconds": 168.15,
  "pages_fetched": 60,
  "cache_hits": 3,
  "valid_records": 60,
  "invalid_records": 1,
  "failed_pages": 1
}
```

The corresponding `errors.json` entry was:

```json
[
  {
    "url": "https://books.toscrape.com/catalogue/this-page-does-not-exist_999999/index.html",
    "reason": "HTTP 404"
  }
]
```

The resulting output contained:

```text
books.json: 60 records
errors.json: 1 failed page
failed_pages: 1
```

The fake page was skipped while the 60 valid book records were preserved.

---

## Why a Browser Is Unnecessary

A browser is unnecessary for this assignment because the required book data is already present in the HTML returned by the server.

A normal HTTP request followed by Beautiful Soup can read the catalogue and product information directly. Using a browser would add unnecessary cost and complexity for this site.

---

## Limitation

This scraper is intentionally limited to the first three catalogue pages of Books to Scrape and depends on the current HTML structure and selectors of the practice site.

It is not intended to be reused unchanged on other websites.

---

## Ethics Note

Scraping should be performed responsibly.

* Use an official API when one exists.
* Never bypass logins, paywalls, access controls, or blocks.
* Collect only the data that is necessary for the task.
* Check a site's rules, terms, and robots guidance before scraping it.
* Use identifying request headers and reasonable delays.
* Avoid sending unnecessary repeated requests.

---

## Project Structure

```text
scraper/
├── src/
│   └── main.py
├── output/
│   ├── books.json
│   ├── errors.json
│   └── run-report.json
├── cache/
├── README.md
└── .gitignore
```

The cache contains downloaded HTML used during development and should not be committed to the public repository.

---

## Submission

This project is the Python implementation of **FlyRank Internship · Backend Track · Week 5 · Assignment A9 — The Polite Scraper**.

The repository contains the scraper source code, sample output, documentation, and evidence of the failure-handling run.
