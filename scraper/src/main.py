from pathlib import Path
import json

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = "PoliteScraper/1.0"
TIMEOUT = 10

CACHE_FILE = Path("cache/catalogue-page-1.html")
OUTPUT_FILE = Path("cache/products.json")


def fetch_catalogue_page():
    # Stage 3: use cached HTML if it already exists
    if CACHE_FILE.exists():
        print("CACHE HIT")
        content = CACHE_FILE.read_bytes()
        print(f"response_size={len(content)} bytes")
        return content

    headers = {
        "User-Agent": USER_AGENT
    }

    try:
        response = requests.get(
            BASE_URL,
            headers=headers,
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Request failed: {exc}") from exc

    if response.status_code != 200:
        raise RuntimeError(
            f"Fetch failed: HTTP {response.status_code}"
        )

    content = response.content

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_bytes(content)

    print(f"response_size={len(content)} bytes")
    print(f"saved={CACHE_FILE}")

    return content


def parse_products(content):
    soup = BeautifulSoup(content, "html.parser")

    product_elements = soup.select("article.product_pod")

    products = []

    for product in product_elements:
        title_element = product.select_one("h3 a")
        price_element = product.select_one(".price_color")
        availability_element = product.select_one(
            ".availability"
        )
        rating_element = product.select_one(".star-rating")

        title = title_element.get("title", "").strip()
        price = price_element.get_text(strip=True)
        availability = availability_element.get_text(
            " ",
            strip=True,
        )

        rating_classes = rating_element.get("class", [])
        rating_map = {
            "One": 1,
            "Two": 2,
            "Three": 3,
            "Four": 4,
            "Five": 5,
        }

        rating = 0

        for class_name in rating_classes:
            if class_name in rating_map:
                rating = rating_map[class_name]
                break

        url = title_element.get("href", "")

        products.append(
            {
                "title": title,
                "price": price,
                "availability": availability,
                "rating": rating,
                "url": url,
            }
        )

    print(f"products={len(products)}")

    return products


def save_products(products):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_FILE.write_text(
        json.dumps(products, indent=2),
        encoding="utf-8",
    )

    print(f"saved={OUTPUT_FILE}")


def main():
    content = fetch_catalogue_page()

    products = parse_products(content)

    save_products(products)


if __name__ == "__main__":
    main()