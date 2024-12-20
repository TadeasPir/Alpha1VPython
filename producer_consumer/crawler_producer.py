import threading
import time
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from queue import Queue
import re


class CrawlerProducer(threading.Thread):
    def __init__(self, name: str, queue: Queue, produce_interval: float, start_urls: list):
        super().__init__(name=name)
        self.queue = queue
        self.produce_interval = produce_interval
        self.start_urls = start_urls
        self.visited_urls = set()
        self._stop_event = threading.Event()
        self.url_queue = list(start_urls)

    def is_valid_article_url(self, url):
        valid_domains = ['novinky.cz', 'idnes.cz', 'ctk.cz']
        parsed_url = urlparse(url)

        domain_match = any(domain in parsed_url.netloc for domain in valid_domains)

        file_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.mp4']
        is_file = any(url.lower().endswith(ext) for ext in file_extensions)

        article_patterns = {
            'novinky.cz': r'/clanek/',
            'idnes.cz': r'/zpravy/',
            'ctk.cz': r'/clanek/'
        }

        is_article = any(
            re.search(pattern, url)
            for site, pattern in article_patterns.items()
            if site in parsed_url.netloc
        )

        return domain_match and is_article and not is_file

    def extract_article_data(self, url, soup):
        article_data = {
            'url': url,
            'title': self.extract_title(soup),
            'content': self.extract_content(soup),
            'created_at': self.extract_date(soup),
            'source_website': urlparse(url).netloc
        }
        return article_data

    def extract_title(self, soup):
        title_selectors = ['h1.article-title', 'h1.title', 'h1', 'title']
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                return title_elem.get_text(strip=True)
        return "Title not found"

    def extract_content(self, soup):
        content_selectors = ['div.article-content', 'div.content', 'article', 'div.text']
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                return content_elem.get_text(separator=' ', strip=True)
        return "Content not found"

    def extract_date(self, soup):
        from datetime import datetime
        date_selectors = [
            'meta[property="article:published_time"]',
            'time[datetime]',
            'meta[name="date"]'
        ]

        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_str = date_elem.get('content') or date_elem.get('datetime')
                try:
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00')).isoformat()
                except (ValueError, TypeError):
                    pass
        return datetime.now().isoformat()

    def extract_links(self, soup, base_url):
        links = set()
        for link in soup.find_all('a', href=True):
            absolute_url = urljoin(base_url, link['href'])
            if self.is_valid_article_url(absolute_url):
                links.add(absolute_url)
        return links

    def crawl_url(self, url):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract article data
            article_data = self.extract_article_data(url, soup)

            # Extract new links and add them to url_queue
            new_links = self.extract_links(soup, url)
            self.url_queue.extend(list(new_links - self.visited_urls))

            return article_data

        except requests.RequestException as e:
            logging.error(f"{self.name} failed to crawl {url}: {e}")
            return None

    def run(self):
        logging.info(f"{self.name} started.")
        while not self._stop_event.is_set():
            if not self.url_queue:
                # If no URLs left, restart with start_urls
                self.url_queue = list(self.start_urls)

            current_url = self.url_queue.pop(0)

            if current_url not in self.visited_urls:
                article_data = self.crawl_url(current_url)
                if article_data:
                    try:
                        self.queue.put(article_data, timeout=1)
                        self.visited_urls.add(current_url)
                        logging.info(f"{self.name} produced article: {article_data['title']}")
                    except Exception as e:
                        logging.error(f"{self.name} failed to put article in queue: {e}")

            time.sleep(self.produce_interval)
        logging.info(f"{self.name} stopped.")

    def stop(self):
        self._stop_event.set()