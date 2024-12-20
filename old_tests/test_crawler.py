import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open, call
import threading
import queue
import logging
import json
import yaml
import os
from bs4 import BeautifulSoup
from datetime import datetime
from queue import Queue

# Import the classes we're testing
from producer_consumer.config import Config
from producer_consumer.app import CrawlerApp
from producer_consumer.crawler_producer import CrawlerProducer
from producer_consumer.crawler_consumer import ArticleConsumer
from producer_consumer.utils import setup_logging


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.test_config = {
            'producer': {
                'count': 2,
                'produce_interval': 1.0,
                'start_urls': ['http://test.com']
            },
            'consumer': {
                'count': 3,
                'consume_interval': 0.5,
                'output_dir': 'test_output'
            },
            'queue': {
                'max_size': 100
            },
            'logging': {
                'level': 'INFO',
                'file': 'test.log'
            }
        }

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_config_loading(self, mock_yaml_load, mock_file):
        mock_yaml_load.return_value = self.test_config
        config = Config('dummy_path.yaml')

        self.assertEqual(config.producer_count, 2)
        self.assertEqual(config.produce_interval, 1.0)
        self.assertEqual(config.start_urls, ['http://test.com'])
        self.assertEqual(config.consumer_count, 3)
        self.assertEqual(config.consume_interval, 0.5)
        self.assertEqual(config.output_dir, 'test_output')
        self.assertEqual(config.queue_max_size, 100)
        self.assertEqual(config.logging_level, 'INFO')
        self.assertEqual(config.logging_file, 'test.log')

    @patch('os.path.exists')
    def test_config_file_not_found(self, mock_exists):
        mock_exists.return_value = False
        with self.assertRaises(FileNotFoundError):
            Config('nonexistent.yaml')

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_config_missing_required_fields(self, mock_yaml_load, mock_file):
        incomplete_config = {
            'producer': {
                'count': 2
                # Missing other required fields
            }
        }
        mock_yaml_load.return_value = incomplete_config
        config = Config('dummy_path.yaml')

        # Test that accessing missing fields raises AttributeError
        with self.assertRaises(KeyError):
            _ = config.produce_interval


class TestCrawlerProducer(unittest.TestCase):
    def setUp(self):
        self.queue = Queue(maxsize=10)
        self.start_urls = ['http://test.com']
        self.producer = CrawlerProducer(
            name='TestProducer',
            queue=self.queue,
            produce_interval=0.1,
            start_urls=self.start_urls
        )

    def test_initialization(self):
        self.assertEqual(self.producer.name, 'TestProducer')
        self.assertEqual(self.producer.start_urls, self.start_urls)
        self.assertEqual(len(self.producer.visited_urls), 0)
        self.assertEqual(self.producer.url_queue, self.start_urls)

    def test_is_valid_article_url(self):
        valid_urls = [
            'https://www.novinky.cz/clanek/test',
            'https://www.idnes.cz/zpravy/test',
            'https://www.ctk.cz/clanek/test'
        ]
        invalid_urls = [
            'https://www.example.com/article',
            'https://www.novinky.cz/image.jpg',
            'https://www.idnes.cz/sport'
        ]

        for url in valid_urls:
            self.assertTrue(self.producer.is_valid_article_url(url))
        for url in invalid_urls:
            self.assertFalse(self.producer.is_valid_article_url(url))

    def test_extract_title_with_various_selectors(self):
        test_cases = [
            ('<h1 class="article-title">Test 1</h1>', 'Test 1'),
            ('<h1 class="title">Test 2</h1>', 'Test 2'),
            ('<h1>Test 3</h1>', 'Test 3'),
            ('<title>Test 4</title>', 'Test 4'),
            ('<div>No Title Here</div>', 'Title not found')
        ]

        for html, expected in test_cases:
            soup = BeautifulSoup(html, 'html.parser')
            self.assertEqual(self.producer.extract_title(soup), expected)

    def test_extract_content_with_various_selectors(self):
        test_cases = [
            ('<div class="article-content">Content 1</div>', 'Content 1'),
            ('<div class="content">Content 2</div>', 'Content 2'),
            ('<article>Content 3</article>', 'Content 3'),
            ('<div class="text">Content 4</div>', 'Content 4'),
            ('<div>No Content Here</div>', 'Content not found')
        ]

        for html, expected in test_cases:
            soup = BeautifulSoup(html, 'html.parser')
            self.assertEqual(self.producer.extract_content(soup), expected)

    def test_extract_date_with_various_formats(self):
        test_cases = [
            ('<meta property="article:published_time" content="2024-01-01T12:00:00Z">',),
            ('<time datetime="2024-01-01T12:00:00Z">',),
            ('<meta name="date" content="2024-01-01T12:00:00Z">',)
        ]

        for html in test_cases:
            soup = BeautifulSoup(html, 'html.parser')
            result = self.producer.extract_date(soup)
            self.assertIsNotNone(result)
            self.assertTrue(isinstance(result, str))
            # Verify it's a valid ISO format date
            try:
                datetime.fromisoformat(result.replace('Z', '+00:00'))
            except ValueError:
                self.fail(f"Invalid date format: {result}")

    def test_extract_links_with_various_scenarios(self):
        html = '''
        <html>
            <body>
                <a href="/clanek/1">Valid Article 1</a>
                <a href="https://www.novinky.cz/clanek/2">Valid Article 2</a>
                <a href="/image.jpg">Invalid Image</a>
                <a href="https://www.example.com/article">Invalid Domain</a>
                <a href="">Empty Link</a>
                <a>No Href</a>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        base_url = 'https://www.novinky.cz'

        links = self.producer.extract_links(soup, base_url)
        self.assertIsInstance(links, set)
        self.assertTrue(any('clanek/1' in link for link in links))
        self.assertTrue(any('clanek/2' in link for link in links))
        self.assertFalse(any('image.jpg' in link for link in links))
        self.assertFalse(any('example.com' in link for link in links))

    @patch('requests.get')
    def test_crawl_url_with_network_errors(self, mock_get):
        # Test timeout
        mock_get.side_effect = requests.Timeout()
        result = self.producer.crawl_url('https://www.novinky.cz/test')
        self.assertIsNone(result)

        # Test connection error
        mock_get.side_effect = requests.ConnectionError()
        result = self.producer.crawl_url('https://www.novinky.cz/test')
        self.assertIsNone(result)

        # Test HTTP error
        mock_get.side_effect = requests.HTTPError()
        result = self.producer.crawl_url('https://www.novinky.cz/test')
        self.assertIsNone(result)


class TestArticleConsumer(unittest.TestCase):
    def setUp(self):
        self.queue = Queue(maxsize=10)
        self.output_dir = 'test_output'
        self.consumer = ArticleConsumer(
            name='TestConsumer',
            queue=self.queue,
            consume_interval=0.1,
            output_dir=self.output_dir
        )

    def test_save_article_with_duplicate_detection(self):
        # Test multiple variations of the same article
        original_article = {
            'url': 'https://test.com/article1',
            'title': 'Test Article',
            'content': 'Original content'
        }

        duplicate_with_different_content = {
            'url': 'https://test.com/article1',
            'title': 'Updated Title',
            'content': 'Different content'
        }

        different_article = {
            'url': 'https://test.com/article2',
            'title': 'Different Article',
            'content': 'Different content'
        }

        # Save original article
        self.consumer.save_article(original_article)
        self.assertEqual(len(self.consumer.articles), 1)

        # Try to save duplicate
        self.consumer.save_article(duplicate_with_different_content)
        self.assertEqual(len(self.consumer.articles), 1)
        # Verify original content wasn't overwritten
        self.assertEqual(self.consumer.articles[0]['content'], 'Original content')

        # Save different article
        self.consumer.save_article(different_article)
        self.assertEqual(len(self.consumer.articles), 2)

    @patch('builtins.open', new_callable=mock_open)
    def test_save_to_file_with_unicode(self, mock_file):
        test_articles = [
            {
                'url': 'https://test.com/1',
                'title': 'Test článek',  # Czech characters
                'content': 'Zkušební obsah s diakritikou ěščřžýáíé'
            }
        ]
        self.consumer.articles = test_articles

        self.consumer.save_to_file()
        mock_file.assert_called_once_with(
            os.path.join(self.output_dir, 'articles.json'),
            'w',
            encoding='utf-8'
        )

    def test_run_method_error_handling(self):
        # Test handling of various queue errors
        with patch.object(self.queue, 'get', side_effect=Exception('Test error')), \
                patch('logging.warning') as mock_log:
            # Start consumer and let it process one iteration
            self.consumer.start()
            time.sleep(0.2)
            self.consumer.stop()
            self.consumer.join()

            # Verify error was logged
            mock_log.assert_called_with(ANY)


if __name__ == '__main__':
    unittest.main()