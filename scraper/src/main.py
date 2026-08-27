from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urljoin
import json
import time

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, HttpUrl, ValidationError


# --------------------------------------------------
# Paths and settings
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

BASE_URL = "https://books.toscrape.com/catalogue/page-1.html"
SITE_BASE_URL = "https://books.toscrape.com/catalogue/"

USER_AGENT = "PoliteScraper/1.0"
TIMEOUT = 10
DELAY_SECONDS = 0.5

CACHE_DIR = BASE_DIR / "cache"
OUTPUT_DIR = BASE_DIR / "output"

BOOKS_FILE = OUTPUT_DIR / "books.json"
ERRORS_FILE = OUTPUT_DIR / "errors.json"
REPORT_FILE = OUTPUT_DIR / "run-report.json"


# --------------------------------------------------
# Run statistics
# --------------------------------------------------

stats = {
    "pages_fetched": 0,
    "cache_hits": 0,
    "valid_records": 0,
    "invalid_records": 0,
    "failed_pages": 0,
}


# --------------------------------------------------
# Schema
# --------------------------------------------------

class BookRecord(BaseModel):
    title: str
    product_url: HttpUrl
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: str
    description: str | None
    source_page: HttpUrl
    fetched_at: str


# --------------------------------------------------
# URLs
# --------------------------------------------------

def get_page_url(page_number):
    return (
        f"https://books.toscrape.com/catalogue/"
        f"page-{page_number}.html"
    )


# --------------------------------------------------
# Fetch catalogue pages
# --------------------------------------------------

def fetch_catalogue_page(page_number):
    cache_file = (
        CACHE_DIR
        / f"catalogue-page-{page_number}.html"
    )

    if cache_file.exists():
        print("CACHE HIT")

        stats["cache_hits"] += 1

        content = cache_file.read_bytes()

        print(f"response_size={len(content)} bytes")

        return content

    headers = {
        "User-Agent": USER_AGENT
    }

    try:
        time.sleep(DELAY_SECONDS)

        response = requests.get(
            get_page_url(page_number),
            headers=headers,
            timeout=TIMEOUT,
        )

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Request failed: {exc}"
        ) from exc

    if response.status_code != 200:
        raise RuntimeError(
            f"Fetch failed: HTTP {response.status_code}"
        )

    stats["pages_fetched"] += 1

    content = response.content

    cache_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    cache_file.write_bytes(content)

    print(f"response_size={len(content)} bytes")
    print(f"saved={cache_file}")

    return content


# --------------------------------------------------
# Discover book URLs
# --------------------------------------------------

def discover_book_urls():
    all_urls = []
    current_page = 1

    while current_page <= 3:
        print(
            f"Discovering catalogue page {current_page}..."
        )

        content = fetch_catalogue_page(current_page)

        soup = BeautifulSoup(
            content,
            "html.parser",
        )

        for link in soup.select(
            "article.product_pod h3 a"
        ):
            href = link.get("href")

            if href:
                absolute_url = urljoin(
                    get_page_url(current_page),
                    href,
                )

                all_urls.append(
                    absolute_url
                )

        next_link = soup.select_one(
            "li.next a"
        )

        if not next_link:
            break

        current_page += 1

    unique_urls = list(
        dict.fromkeys(all_urls)
    )

    print(
        f"catalogue_pages={current_page}"
    )

    print(
        f"discovered={len(all_urls)}"
    )

    print(
        f"unique_urls={len(unique_urls)}"
    )

    return unique_urls


# --------------------------------------------------
# Cache filename for detail pages
# --------------------------------------------------

def detail_cache_file(product_url):
    safe_name = (
        product_url
        .rstrip("/")
        .split("/")[-2]
    )

    return (
        CACHE_DIR
        / "details"
        / f"{safe_name}.html"
    )


# --------------------------------------------------
# Fetch individual book page
# --------------------------------------------------

def fetch_book_page(product_url):
    cache_file = detail_cache_file(
        product_url
    )

    if cache_file.exists():
        stats["cache_hits"] += 1

        content = cache_file.read_bytes()

        print(
            f"CACHE HIT detail: "
            f"{product_url}"
        )

        return content

    headers = {
        "User-Agent": USER_AGENT
    }

    last_error = None

    for attempt in range(2):
        try:
            time.sleep(DELAY_SECONDS)

            response = requests.get(
                product_url,
                headers=headers,
                timeout=TIMEOUT,
            )

            # Do not retry 403 or 404.
            if response.status_code in (403, 404):
                raise RuntimeError(
                    f"HTTP {response.status_code}"
                )

            # Retry server errors once.
            if response.status_code >= 500:
                last_error = RuntimeError(
                    f"HTTP {response.status_code}"
                )

                if attempt == 0:
                    time.sleep(1)
                    continue

                raise last_error

            if response.status_code != 200:
                raise RuntimeError(
                    f"HTTP {response.status_code}"
                )

            content = response.content

            stats["pages_fetched"] += 1

            cache_file.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            cache_file.write_bytes(content)

            print(
                f"FETCH detail: {product_url}"
            )

            return content

        except requests.Timeout as exc:
            last_error = RuntimeError(
                f"Timeout: {exc}"
            )

            if attempt == 0:
                time.sleep(1)
                continue

            raise last_error

        except requests.RequestException as exc:
            last_error = RuntimeError(
                f"Request failed: {exc}"
            )

            if attempt == 0:
                time.sleep(1)
                continue

            raise last_error

    raise last_error


# --------------------------------------------------
# Extract one book
# --------------------------------------------------

def extract_book(
    content,
    product_url,
    source_page,
):
    soup = BeautifulSoup(
        content,
        "html.parser",
    )

    product = soup.select_one(
        "article.product_page"
    )

    if not product:
        raise ValueError(
            "Product area not found"
        )

    title_element = product.select_one(
        "h1"
    )

    price_element = product.select_one(
        ".price_color"
    )

    availability_element = product.select_one(
        ".availability"
    )

    rating_element = product.select_one(
        ".star-rating"
    )

    description_element = soup.select_one(
        "#product_description + p"
    )

    if not title_element:
        raise ValueError(
            "Missing title"
        )

    if not price_element:
        raise ValueError(
            "Missing price"
        )

    if not availability_element:
        raise ValueError(
            "Missing availability"
        )

    if not rating_element:
        raise ValueError(
            "Missing rating"
        )

    title = title_element.get_text(
        strip=True
    )

    price_text = price_element.get_text(
        strip=True
    )

    availability_text = (
        availability_element.get_text(
            " ",
            strip=True,
        )
    )

    rating_classes = rating_element.get(
        "class",
        [],
    )

    rating_text = ""

    rating_names = {
        "One",
        "Two",
        "Three",
        "Four",
        "Five",
    }

    for class_name in rating_classes:
        if class_name in rating_names:
            rating_text = class_name
            break

    description = None

    if description_element:
        description = description_element.get_text(
            " ",
            strip=True,
        )

    fetched_at = datetime.now(
        timezone.utc
    ).isoformat()

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at,
    }


# --------------------------------------------------
# Normalize price
# --------------------------------------------------

def normalize_price(price_text):
    return float(
        price_text
        .replace("£", "")
        .strip()
    )


# --------------------------------------------------
# Validate and normalize
# --------------------------------------------------

def validate_record(raw_record):
    record = dict(raw_record)

    record["price_gbp"] = normalize_price(
        record["price_text"]
    )

    validated = BookRecord(
        **record
    )

    return validated.model_dump(
        mode="json"
    )


# --------------------------------------------------
# Save JSON
# --------------------------------------------------

def save_json(path, data):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


# --------------------------------------------------
# Main scraping pipeline
# --------------------------------------------------

def scrape_books():
    urls = discover_book_urls()

    # Deliberately add one fake URL.
    # This tests that one broken page
    # does not kill the whole run.
    test_bad_url = (
        "https://books.toscrape.com/"
        "catalogue/this-page-does-not-exist_999999/"
        "index.html"
    )

    urls.append(test_bad_url)

    valid_records = []
    errors = []

    seen_urls = set()

    for index, product_url in enumerate(
        urls,
        start=1,
    ):
        print(
            f"Book {index}/{len(urls)}"
        )

        if product_url in seen_urls:
            continue

        seen_urls.add(product_url)

        source_page = get_page_url(
            ((index - 1) // 20) + 1
        )

        try:
            content = fetch_book_page(
                product_url
            )

            raw_record = extract_book(
                content,
                product_url,
                source_page,
            )

            validated = validate_record(
                raw_record
            )

            valid_records.append(
                validated
            )

        except (
            RuntimeError,
            ValueError,
            ValidationError,
        ) as exc:

            print(
                f"FAILED: {product_url}"
            )

            print(
                f"REASON: {exc}"
            )

            errors.append(
                {
                    "url": product_url,
                    "reason": str(exc),
                }
            )

            stats["failed_pages"] += 1
            stats["invalid_records"] += 1

    stats["valid_records"] = len(
        valid_records
    )

    return valid_records, errors


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    # Reset stats for this run.
    for key in stats:
        stats[key] = 0

    start = time.monotonic()

    start_time = datetime.now(
        timezone.utc
    ).isoformat()

    try:
        books, errors = scrape_books()

        save_json(
            BOOKS_FILE,
            books,
        )

        save_json(
            ERRORS_FILE,
            errors,
        )

        print(
            f"valid_records={len(books)}"
        )

        print(
            f"invalid_records={len(errors)}"
        )

        print(
            f"failed_pages={stats['failed_pages']}"
        )

        print(
            f"saved={BOOKS_FILE}"
        )

        print(
            f"saved={ERRORS_FILE}"
        )

    finally:
        duration = (
            time.monotonic() - start
        )

        report = {
            "start_time": start_time,
            "duration_seconds": round(
                duration,
                2,
            ),
            "pages_fetched": stats[
                "pages_fetched"
            ],
            "cache_hits": stats[
                "cache_hits"
            ],
            "valid_records": stats[
                "valid_records"
            ],
            "invalid_records": stats[
                "invalid_records"
            ],
            "failed_pages": stats[
                "failed_pages"
            ],
        }

        save_json(
            REPORT_FILE,
            report,
        )

        print(
            f"saved={REPORT_FILE}"
        )


if __name__ == "__main__":
    main()