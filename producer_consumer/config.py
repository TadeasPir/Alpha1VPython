import yaml
import os

class Config:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self._config = self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file {self.config_path} not found.")
        with open(self.config_path, 'r') as file:
            return yaml.safe_load(file)

    @property
    def producer_count(self):
        return self._config['producer']['count']

    @property
    def produce_interval(self):
        return self._config['producer']['produce_interval']

    @property
    def start_urls(self):
        return self._config['producer']['start_urls']

    @property
    def consumer_count(self):
        return self._config['consumer']['count']

    @property
    def consume_interval(self):
        return self._config['consumer']['consume_interval']

    @property
    def output_dir(self):
        return self._config['consumer']['output_dir']

    @property
    def queue_max_size(self):
        return self._config['queue']['max_size']

    @property
    def logging_level(self):
        return self._config['logging']['level']

    @property
    def logging_file(self):
        return self._config['logging']['file']