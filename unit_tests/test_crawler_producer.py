import unittest
from unittest.mock import Mock, patch, MagicMock
from bs4 import BeautifulSoup
from queue import Queue
from datetime import datetime
import requests

from producer_consumer.crawler_producer import CrawlerProducer


class TestCrawlerProducer(unittest.TestCase):
    def setUp(self):
        self.queue = Queue()
        self.start_urls = ['https://novinky.cz/clanek/1', 'https://idnes.cz/zpravy/2']
        self.crawler = CrawlerProducer(
            name="TestCrawler",
            queue=self.queue,
            produce_interval=0.1,
            start_urls=self.start_urls
        )

    def test_init(self):
        """Test the initialization of CrawlerProducer"""
        self.assertEqual(self.crawler.name, "TestCrawler")
        self.assertEqual(self.crawler.produce_interval, 0.1)
        self.assertEqual(self.crawler.start_urls, self.start_urls)
        self.assertEqual(self.crawler.visited_urls, set())
        self.assertEqual(self.crawler.url_queue, self.start_urls)

    def test_is_valid_article_url_positive(self):
        """Test valid article URLs are correctly identified"""
        valid_urls = [
            'https://novinky.cz/clanek/test-article',
            'https://idnes.cz/zpravy/domaci/article',
            'https://ctk.cz/clanek/news'
        ]
        for url in valid_urls:
            self.assertTrue(
                self.crawler.is_valid_article_url(url),
                f"URL should be valid: {url}"
            )

    def test_is_valid_article_url_negative(self):
        """Test invalid article URLs are correctly rejected"""
        invalid_urls = [
            'https://example.com/article',
            'https://novinky.cz/image.jpg',
            'https://idnes.cz/sport',
            'https://novinky.cz',
            'https://ctk.cz/image.pdf'
        ]
        for url in invalid_urls:
            self.assertFalse(
                self.crawler.is_valid_article_url(url),
                f"URL should be invalid: {url}"
            )

    def test_extract_title(self):
        """Test title extraction with different HTML structures"""
        test_cases = [
            ('<h1 class="article-title">Test Title 1</h1>', 'Test Title 1'),
            ('<h1 class="title">Test Title 2</h1>', 'Test Title 2'),
            ('<h1>Test Title 3</h1>', 'Test Title 3'),
            ('<title>Test Title 4</title>', 'Test Title 4'),
            ('<div>No Title Here</div>', 'Title not found')
        ]

        for html, expected_title in test_cases:
            soup = BeautifulSoup(html, 'html.parser')
            self.assertEqual(
                self.crawler.extract_title(soup),
                expected_title,
                f"Failed to extract title from HTML: {html}"
            )

    def test_extract_content(self):
        """Test content extraction with different HTML structures"""
        test_cases = [
            ('<div class="article-content">Test Content 1</div>', 'Test Content 1'),
            ('<div class="content">Test Content 2</div>', 'Test Content 2'),
            ('<article>Test Content 3</article>', 'Test Content 3'),
            ('<div class="text">Test Content 4</div>', 'Test Content 4'),
            ('<div>No Content Here</div>', 'Content not found')
        ]

        for html, expected_content in test_cases:
            soup = BeautifulSoup(html, 'html.parser')
            self.assertEqual(
                self.crawler.extract_content(soup),
                expected_content,
                f"Failed to extract content from HTML: {html}"
            )

    def test_extract_date(self):
        """Test date extraction with different HTML structures"""
        current_time = datetime.now().isoformat()
        test_cases = [
            ('<meta property="article:published_time" content="2024-01-01T12:00:00+00:00"/>',
             '2024-01-01T12:00:00+00:00'),
            ('<time datetime="2024-02-01T15:30:00+00:00">Feb 1</time>',
             '2024-02-01T15:30:00+00:00'),
            ('<meta name="date" content="2024-03-01T10:00:00+00:00"/>',
             '2024-03-01T10:00:00+00:00'),
            ('<div>No date here</div>',
             current_time)
        ]

        for html, expected_date in test_cases:
            soup = BeautifulSoup(html, 'html.parser')
            extracted_date = self.crawler.extract_date(soup)
            if expected_date == current_time:
                # For the current time case, just verify it's a valid ISO format
                datetime.fromisoformat(extracted_date)
            else:
                self.assertEqual(
                    extracted_date,
                    expected_date,
                    f"Failed to extract date from HTML: {html}"
                )

    def test_extract_links(self):
        """Test link extraction and validation"""
        html = '''
        <html>
            <body>
                <a href="/clanek/valid1">Valid 1</a>
                <a href="https://novinky.cz/clanek/valid2">Valid 2</a>
                <a href="https://idnes.cz/zpravy/valid3">Valid 3</a>
                <a href="https://example.com/invalid">Invalid</a>
                <a href="https://novinky.cz/image.jpg">Invalid Image</a>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        base_url = 'https://novinky.cz'

        extracted_links = self.crawler.extract_links(soup, base_url)

        expected_links = {
            'https://novinky.cz/clanek/valid1',
            'https://novinky.cz/clanek/valid2',
            'https://idnes.cz/zpravy/valid3'
        }

        self.assertEqual(extracted_links, expected_links)

    @patch('requests.get')
    def test_crawl_url_success(self, mock_get):
        """Test successful URL crawling"""
        mock_response = Mock()
        mock_response.text = '''
            <html>
                <h1 class="article-title">Test Article</h1>
                <div class="article-content">Test Content</div>
                <meta property="article:published_time" content="2024-01-01T12:00:00+00:00"/>
                <a href="https://novinky.cz/clanek/new-article">New Article</a>
            </html>
        '''
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        url = 'https://novinky.cz/clanek/test'
        result = self.crawler.crawl_url(url)

        self.assertEqual(result['url'], url)
        self.assertEqual(result['title'], 'Test Article')
        self.assertEqual(result['content'], 'Test Content')
        self.assertEqual(result['created_at'], '2024-01-01T12:00:00+00:00')
        self.assertEqual(result['source_website'], 'novinky.cz')

    @patch('requests.get')
    def test_crawl_url_failure(self, mock_get):
        """Test URL crawling failure handling"""
        mock_get.side_effect = requests.RequestException("Test error")

        result = self.crawler.crawl_url('https://novinky.cz/clanek/test')
        self.assertIsNone(result)

    @patch('time.sleep')  # Prevent actual sleeping in tests
    def test_run_and_stop(self, mock_sleep):
        """Test the run and stop functionality"""
        with patch.object(self.crawler, 'crawl_url') as mock_crawl:
            mock_crawl.return_value = {
                'url': 'https://novinky.cz/clanek/test',
                'title': 'Test',
                'content': 'Content',
                'created_at': '2024-01-01T12:00:00+00:00',
                'source_website': 'novinky.cz'
            }

            # Start the crawler
            self.crawler.start()

            # Let it run briefly
            import time
            time.sleep(0.2)

            # Stop the crawler
            self.crawler.stop()
            self.crawler.join(timeout=1)

            # Verify the crawler has stopped
            self.assertFalse(self.crawler.is_alive())

            # Verify that at least one article was processed
            self.assertGreater(len(self.crawler.visited_urls), 0)
            self.assertFalse(self.queue.empty())


if __name__ == '__main__':
    unittest.main()