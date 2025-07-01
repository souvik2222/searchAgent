import asyncio
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests

def extract_main_content(soup):
    # Try <article>
    article = soup.find('article')
    if article:
        return ' '.join(article.stripped_strings), 'article'
    # Try <main>
    main = soup.find('main')
    if main:
        return ' '.join(main.stripped_strings), 'main'
    # Try largest <div>
    divs = soup.find_all('div')
    if divs:
        largest = max(divs, key=lambda d: len(d.get_text()))
        return ' '.join(largest.stripped_strings), 'largest_div'
    # Fallback: all text
    return ' '.join(soup.stripped_strings), 'all_text'

def scrape_urls(urls, num_results, debug=False):
    results = []
    for url in urls[:num_results]:
        try:
            resp = requests.get(url, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            title = soup.title.string.strip() if soup.title and soup.title.string else url
            text, used = extract_main_content(soup)
            if debug:
                print(f"[DEBUG] Used {used} for {url}, text length: {len(text)}")
            results.append((url, title, text[:5000]))  # Limit to 5000 chars
        except Exception as e:
            if debug:
                print(f"[DEBUG] Error scraping {url}: {e}")
            results.append((url, url, f'Error scraping: {e}'))
    return results

def search_and_scrape(query: str, num_results: int = 5, debug: bool = False):
    """
    Searches DuckDuckGo for the query, scrapes the top result URLs, and returns a list of (url, title, text) tuples.
    Falls back to Google if DuckDuckGo fails.
    """
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        # Try DuckDuckGo
        page.goto(f'https://duckduckgo.com/?q={query.replace(" ", "+")}&t=h_&ia=web')
        try:
            page.wait_for_selector('a[data-testid="result-title-a"], a.result__a', timeout=10000)
            links = page.query_selector_all('a[data-testid="result-title-a"], a.result__a')
            urls = [a.get_attribute('href') for a in links]
            urls = [u for u in urls if u and u.startswith('http')]
            if urls:
                browser.close()
                return scrape_urls(urls, num_results, debug=debug)
        except Exception as e:
            if debug:
                print(f"[DEBUG] DuckDuckGo search failed: {e}")
        # Fallback to Google
        if debug:
            print("[DEBUG] Falling back to Google search...")
        page.goto(f'https://www.google.com/search?q={query.replace(" ", "+")}')
        try:
            page.wait_for_selector('a h3', timeout=10000)
            links = page.query_selector_all('a h3')
            urls = []
            for h3 in links:
                a = h3.evaluate_handle('node => node.parentElement')
                href = a.get_property('href').json_value()
                if href and href.startswith('http') and 'google.com' not in href:
                    urls.append(href)
            if urls:
                browser.close()
                return scrape_urls(urls, num_results, debug=debug)
        except Exception as e:
            if debug:
                print(f"[DEBUG] Google search failed: {e}")
        browser.close()
    return [] 