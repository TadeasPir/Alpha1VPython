import threading
import time
import logging
import json
from queue import Queue
import os


class ArticleConsumer(threading.Thread):
    def __init__(self, name: str, queue: Queue, consume_interval: float, output_dir: str = 'articles'):
        super().__init__(name=name)
        self.queue = queue
        self.consume_interval = consume_interval
        self._stop_event = threading.Event()
        self.output_dir = output_dir
        self.articles = []
        self.setup_output_dir()

    def setup_output_dir(self):
        os.makedirs(self.output_dir, exist_ok=True)
        self.articles_file = os.path.join(self.output_dir, 'articles.json')

        # Load existing articles if file exists
        if os.path.exists(self.articles_file):
            try:
                with open(self.articles_file, 'r', encoding='utf-8') as f:
                    self.articles = json.load(f)
            except json.JSONDecodeError:
                self.articles = []

    def save_article(self, article_data):
        # Check for duplicates based on URL
        if not any(article['url'] == article_data['url'] for article in self.articles):
            self.articles.append(article_data)
            logging.info(f"{self.name} saved article: {article_data['title']}")

            # Save to file every 10 articles
            if len(self.articles) % 10 == 0:
                self.save_to_file()

    def save_to_file(self):
        try:
            with open(self.articles_file, 'w', encoding='utf-8') as f:
                json.dump(self.articles, f, ensure_ascii=False, indent=2)
            logging.info(f"{self.name} saved {len(self.articles)} articles to {self.articles_file}")
        except Exception as e:
            logging.error(f"{self.name} failed to save articles to file: {e}")

    def run(self):
        logging.info(f"{self.name} started.")
        while not self._stop_event.is_set():
            try:
                article = self.queue.get(timeout=10)
                self.save_article(article)
                self.queue.task_done()
            except Exception as e:
                if not isinstance(e, Queue.Empty):
                    logging.warning(f"{self.name} failed to process article: {e}")
            time.sleep(self.consume_interval)

        # Save remaining articles before stopping
        self.save_to_file()
        logging.info(f"{self.name} stopped.")

    def stop(self):
        self._stop_event.set()