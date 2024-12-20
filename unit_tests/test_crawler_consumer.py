import unittest
from unittest.mock import Mock, patch, mock_open
from queue import Queue
import json
import os
import time
from producer_consumer.crawler_consumer import ArticleConsumer


class TestArticleConsumer(unittest.TestCase):
    def setUp(self):
        self.queue = Queue()
        self.test_output_dir = 'test_articles'
        self.consumer = ArticleConsumer(
            name="TestConsumer",
            queue=self.queue,
            consume_interval=0.1,
            output_dir=self.test_output_dir
        )

        # Sample article data for testing
        self.sample_article = {
            'url': 'https://novinky.cz/clanek/test',
            'title': 'Test Article',
            'content': 'Test Content',
            'created_at': '2024-01-01T12:00:00+00:00',
            'source_website': 'novinky.cz'
        }

    def tearDown(self):
        # Clean up test directory after tests
        if os.path.exists(self.test_output_dir):
            for file in os.listdir(self.test_output_dir):
                os.remove(os.path.join(self.test_output_dir, file))
            os.rmdir(self.test_output_dir)

    def test_init(self):
        """Test the initialization of ArticleConsumer"""
        self.assertEqual(self.consumer.name, "TestConsumer")
        self.assertEqual(self.consumer.consume_interval, 0.1)
        self.assertEqual(self.consumer.output_dir, self.test_output_dir)
        self.assertEqual(self.consumer.articles, [])
        self.assertTrue(os.path.exists(self.test_output_dir))

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_setup_output_dir_with_existing_file(self, mock_file, mock_exists):
        """Test setup_output_dir when articles.json already exists"""
        mock_exists.return_value = True
        existing_articles = [
            {
                'url': 'https://novinky.cz/clanek/existing',
                'title': 'Existing Article'
            }
        ]
        mock_file.return_value.read.return_value = json.dumps(existing_articles)

        consumer = ArticleConsumer("TestConsumer", Queue(), 0.1, self.test_output_dir)
        self.assertEqual(consumer.articles, existing_articles)

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_setup_output_dir_with_corrupted_file(self, mock_file, mock_exists):
        """Test setup_output_dir with corrupted articles.json"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = "corrupted json data"

        consumer = ArticleConsumer("TestConsumer", Queue(), 0.1, self.test_output_dir)
        self.assertEqual(consumer.articles, [])

    def test_save_article_new(self):
        """Test saving a new article"""
        self.consumer.save_article(self.sample_article)
        self.assertEqual(len(self.consumer.articles), 1)
        self.assertEqual(self.consumer.articles[0], self.sample_article)

    def test_save_article_duplicate(self):
        """Test saving a duplicate article"""
        self.consumer.save_article(self.sample_article)
        self.consumer.save_article(self.sample_article)
        self.assertEqual(len(self.consumer.articles), 1)

    def test_save_article_different_urls(self):
        """Test saving articles with different URLs"""
        article1 = self.sample_article.copy()
        article2 = self.sample_article.copy()
        article2['url'] = 'https://novinky.cz/clanek/test2'

        self.consumer.save_article(article1)
        self.consumer.save_article(article2)
        self.assertEqual(len(self.consumer.articles), 2)



    @patch('builtins.open')
    def test_save_to_file_error(self, mock_file):
        """Test error handling when saving to file fails"""
        mock_file.side_effect = IOError("Test error")
        self.consumer.articles = [self.sample_article]

        # Should not raise exception
        self.consumer.save_to_file()



    def test_save_article_batch(self):
        """Test saving multiple articles and automatic file saving"""
        # Create 15 different articles
        articles = []
        for i in range(15):
            article = self.sample_article.copy()
            article['url'] = f'https://novinky.cz/clanek/test{i}'
            articles.append(article)

        # Mock save_to_file to track calls
        self.consumer.save_to_file = Mock()

        # Save articles
        for article in articles:
            self.consumer.save_article(article)

        # Verify save_to_file was called at least once (after 10 articles)
        self.consumer.save_to_file.assert_called()
        self.assertEqual(len(self.consumer.articles), 15)






if __name__ == '__main__':
    unittest.main()