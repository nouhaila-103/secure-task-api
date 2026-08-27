from pathlib import Path
import requests
from bs4 import BeautifulSoup


BASE_URL = "https://books.toscrape.com/catalogue/page-1.html"

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
CACHE_FILE = CACHE_DIR / "catalogue-page-1.html"

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/nouhaila-103/flyrank-assignment1)"

TIMEOUT = 10


def fetch_catalogue_page():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Development should use the cached copy when available.
    if CACHE_FILE.exists():
        content = CACHE_FILE.read_bytes()

        print("CACHE HIT")
        print(f"response_size={len(content)} bytes")

        return content

    print(f"FETCH {BASE_URL}")

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

    CACHE_FILE.write_bytes(content)

    print(f"response_size={len(content)} bytes")
    print(f"saved={CACHE_FILE}")

    return content


RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}


def parse_catalogue_page():
    html = CACHE_FILE.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    soup = BeautifulSoup(html, "html.parser")

    products = []

    for card in soup.select("article.product_pod"):
        title_link = card.select_one("h3 a")
        price = card.select_one("p.price_color")
        availability = card.select_one("p.availability")
        rating = card.select_one("p.star-rating")

        products.append(
            {
                "title": title_link.get("title"),
                "price": price.get_text(strip=True),
                "availability": availability.get_text(strip=True),
                "rating": RATING_MAP[rating.get("class")[1]],
                "url": title_link.get("href"),
            }
        )

    return products
def main():
    fetch_catalogue_page()

    products = parse_catalogue_page()

    print(f"products={len(products)}")
    print(products[0])
    
if __name__ == "__main__":
    main()