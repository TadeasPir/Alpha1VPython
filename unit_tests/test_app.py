
import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open, call, ANY


import requests

import os
from bs4 import BeautifulSoup
from queue import Queue

from producer_consumer.crawler_producer import CrawlerProducer
from producer_consumer.crawler_consumer import ArticleConsumer


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
            'https://www.novinky.cz/clanek/',
            'https://www.idnes.cz/zpravy/',
            'https://www.ctk.cz/clanek/ß'
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
        result = self.producer.crawl_url('https://www.novinky.cz/')
        self.assertIsNone(result)

        # Test connection error
        mock_get.side_effect = requests.ConnectionError()
        result = self.producer.crawl_url('https://www.novinky.cz/')
        self.assertIsNone(result)

        # Test HTTP error
        mock_get.side_effect = requests.HTTPError()
        result = self.producer.crawl_url('https://www.novinky.cz/')
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




if __name__ == '__main__':
    unittest.main()