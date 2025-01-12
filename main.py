import argparse
import logging
import sys
from producer_consumer.config import Config
from producer_consumer.app import CrawlerApp




def main():


    # Load configuration
    try:
        config = Config("config/config.yaml")
    except Exception as e:
        logging.error(f"Error during execution: {e}")


    # Create and run the crawler application
    app = CrawlerApp(config)

    try:
        app.run()
    except Exception as e:
        logging.error(f"Error during execution: {e}")
        app.stop()



if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as e:
        logging.info(f"interuped by keyboard: {e}")