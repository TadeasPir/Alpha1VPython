
# Documentation for Producer-Consumer app

## Overview
This app tackles the Producer-Consumer problem and implements it in creative way using web crawler.


### Key Features:
- **Multithreading:** Separate threads for producing and consuming articles.
- **Configurable:** Customizable through a YAML configuration file.
- **Logging:** Detailed logs of the crawling and processing activities.
- **Persistence:** Articles are saved locally in JSON format.

---

## Application Components

### 1. `app.py` - Main Application Controller

#### Purpose
Manages the entire lifecycle of the application, including initialization, starting, stopping, and graceful shutdown.

#### Key Classes and Methods

- **`CrawlerApp` Class:**
  - `__init__(self, config: Config)`: Initializes queues, producers, and consumers.
  - `_setup(self)`: Configures logging and initializes producers and consumers.
  - `start(self)`: Starts all producers and consumers.
  - `stop(self)`: Stops all threads gracefully.
  - `run(self, run_time: float = None)`: Manages the main application loop.

---

### 2. `config.py` - Configuration Manager

#### Purpose
Loads configuration data from a YAML file, ensuring that application parameters can be easily adjusted.

#### Key Class and Methods

- **`Config` Class:**
  - `__init__(self, config_path: str)`: Initializes the configuration loader.
  - `_load_config(self)`: Reads and parses the YAML file.
  - Various properties like `producer_count`, `consumer_count`, `output_dir`, and `logging_level` provide easy access to configuration values.

---

### 3. `crawler_producer.py` - Article Producer

#### Purpose
Fetches and processes articles from websites using provided start URLs.

#### Key Class and Methods

- **`CrawlerProducer` Class:**
  - `__init__(self, name, queue, produce_interval, start_urls)`: Initializes the producer.
  - `run(self)`: Core loop fetching articles and putting them into the queue.
  - `crawl_url(self, url)`: Fetches and parses articles.
  - `extract_article_data(self, url, soup)`: Extracts article metadata such as title, content, and publication date.
  - `extract_links(self, soup, base_url)`: Finds additional article links.
  - `stop(self)`: Stops the producer thread.

---

### 4. `crawler_consumer.py` - Article Consumer

#### Purpose
Processes and stores articles fetched by producers.

#### Key Class and Methods

- **`ArticleConsumer` Class:**
  - `__init__(self, name, queue, consume_interval, output_dir)`: Initializes the consumer.
  - `run(self)`: Main loop that processes articles from the queue.
  - `save_article(self, article_data)`: Saves articles locally, ensuring no duplicates.
  - `save_to_file(self)`: Writes articles to a JSON file after every 10 articles.
  - `stop(self)`: Stops the consumer thread.

---

### 5. `utils.py` - Utility Functions

#### Purpose
Handles auxiliary tasks such as logging setup.

#### Key Function

- **`setup_logging(level, log_file)`**:
  - Configures loggers with both console and rotating file handlers.
  - Creates necessary directories if missing.

---

## Workflow
1. **Initialization:** The application reads the configuration and initializes logging, producers, and consumers.
2. **Crawling:** Producers fetch articles, extract relevant data, and push them to the queue.
3. **Processing:** Consumers fetch articles from the queue, process, and store them.
4. **Termination:** Graceful shutdown occurs when the application is stopped.

---

## Configuration Format (config.yaml)
```yaml
producer:
  count: 2
  produce_interval: 5
  start_urls:
    - https://example.com/news
consumer:
  count: 2
  consume_interval: 2
  output_dir: articles
queue:
  max_size: 50
logging:
  level: DEBUG
  file: logs/app.log
```
logging has these levels (DEBUG, INFO, WARNING, ERROR)

---

## Best Practices and Recommendations
- **Thread Safety:** Use thread-safe queues for inter-thread communication.
- **Scalability:** Increase the number of producers and consumers for larger-scale crawling.
- **Error Handling:** Implement additional error-handling logic if needed.
- **Data Storage:** Consider using a database for long-term storage.

---

## Future Enhancements
- **Database Integration:** Add support for storing articles in a database.
- **Web Dashboard:** Create a web-based monitoring system.
- **Advanced Crawling Rules:** Introduce more sophisticated crawling rules and filters.

---


## Project Structure

```
web-crawler/
│   app.py              # Main application entry point
│   config.py           # Configuration manager
│   crawler_producer.py # Producer logic
│   crawler_consumer.py # Consumer logic
│   utils.py            # Utility functions
│   requirements.txt    # Project dependencies
├── config/
│   └── config.yaml    # Configuration file
└── logs/              # Log files
└── articles/          # Stored articles
```

---

## License

This project is licensed under the MIT License. See `LICENSE` for more details.

---

## Sources

- [SPŠE Jecná Moodle](https://moodle.spsejecna.cz/mod/page/view.php?id=1940)
- [Python Official Documentation](https://docs.python.org/3/)
- [ChatGPT](https://chatgpt.com/)
- [Claude AI](https://claude.ai/)
- [YouTube Video on Producer-Consumer Problem](https://www.youtube.com/watch?v=Qx3P2wazwI0&)
- [Wikipedia - Producer-Consumer Problem](https://en.wikipedia.org/wiki/Producer%E2%80%93consumer_problem)
- [Educative.io - Producer-Consumer Problem](https://www.educative.io/answers/what-is-the-producer-consumer-problem)

---