import logging
import time
from queue import Queue
from typing import List
from .config import Config
from .crawler_producer import CrawlerProducer
from .crawler_consumer import ArticleConsumer
from .utils import setup_logging


class CrawlerApp:
    def __init__(self, config: Config):
        self.config = config
        self.queue = Queue(maxsize=self.config.queue_max_size)
        self.producers: List[CrawlerProducer] = []
        self.consumers: List[ArticleConsumer] = []
        self._setup()

    def _setup(self):
        setup_logging(self.config.logging_level, self.config.logging_file)
        logging.info("Application setup started.")
        try:
            # Initialize producers with start URLs
            for i in range(self.config.producer_count):
                if self.config.producer_count < 1:
                    logging.error("not enough producerers")
                    self.stop()
                else:
                    producer = CrawlerProducer(
                        name=f"Producer-{i + 1}",
                        queue=self.queue,
                        produce_interval=self.config.produce_interval,
                        start_urls=self.config.start_urls
                    )
                self.producers.append(producer)
                logging.debug(f"Initialized {producer.name}")

            # Initialize consumers with output directory
            for i in range(self.config.consumer_count):
                consumer = ArticleConsumer(
                    name=f"Consumer-{i + 1}",
                    queue=self.queue,
                    consume_interval=self.config.consume_interval,
                    output_dir=self.config.output_dir
                )
                
                self.consumers.append(consumer)
                logging.debug(f"Initialized {consumer.name}")

            logging.info("Application setup completed.")
        except Exception:
            logging.exception("Application setup failed.")

    def start(self):
        logging.info("Starting producers and consumers.")
        for producer in self.producers:
            producer.start()

        for consumer in self.consumers:
            consumer.start()


    def stop(self):
        logging.info("Stopping producers and consumers.")
        for producer in self.producers:
            producer.stop()
        for consumer in self.consumers:
            consumer.stop()
        for producer in self.producers:
            producer.join()
        for consumer in self.consumers:
            consumer.join()
        logging.info("All producers and consumers have been stopped.")

    def run(self):
        try:
            self.start()

            logging.info("Application running indefinitely. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("KeyboardInterrupt received. Shutting down.")
        finally:
            self.stop()