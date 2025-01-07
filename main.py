import argparse
import sys
from producer_consumer.config import Config
from producer_consumer.app import CrawlerApp


def parse_arguments():
    parser = argparse.ArgumentParser(description="Web Crawler with Producer-Consumer Architecture")
    parser.add_argument('-c', '--config',
                        type=str,
                        default='config/config.yaml',
                        help='Path to configuration file.')
    parser.add_argument('-t', '--time',
                        type=float,
                        default=None,
                        help='Run time in seconds. If not specified, runs indefinitely.')
    parser.add_argument('--max-articles',
                        type=int,
                        default=None,
                        help='Maximum number of articles to crawl before stopping.')
    parser.add_argument('--clear-visited',
                        action='store_true',
                        help='Clear the list of visited URLs before starting.')
    return parser.parse_args()


def main():
    args = parse_arguments()

    # Load configuration
    try:
        config = Config(config_path=args.config)
    except Exception as e:
        raise(f"Error loading configuration: {e}")
        sys.exit(1)

    # Create and run the crawler application
    app = CrawlerApp(config)

    try:
        app.run()
    except Exception as e:
        raise(f"Error during execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()