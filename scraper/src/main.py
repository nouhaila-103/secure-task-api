from pathlib import Path
import requests


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


def main():
    fetch_catalogue_page()


if __name__ == "__main__":
    main()