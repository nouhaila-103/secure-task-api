# FlyRank A9 — The Polite Scraper

## Target Classification

### Target

Books to Scrape:

https://books.toscrape.com/

### Why this target is appropriate

Books to Scrape is a public practice sandbox specifically designed for
learning and testing web scraping technologies. It is a fictional bookstore
and does not require JavaScript.

### Scope

This scraper will process only the first three catalogue pages and discover
the 60 books listed on those pages.

### Data collected

For each book, the scraper will collect:

- title
- product URL
- price text
- availability text
- rating text
- description
- source catalogue page
- fetch timestamp

The normalized records will additionally contain a numeric `price_gbp`.

### Robots check

I requested:

https://books.toscrape.com/robots.txt

The response was HTTP 404 Not Found, so no robots file was found.

A missing robots file is not treated as permission to scrape other websites.
This assignment uses Books to Scrape because it is explicitly provided as a
practice scraping sandbox.

### Responsible scraping

I will use an identifying User-Agent, a request timeout, caching, and at least
500 ms between real requests. During development, cached HTML will be used
instead of repeatedly requesting the website.

I will not reuse this code on another site without checking its rules and terms first.