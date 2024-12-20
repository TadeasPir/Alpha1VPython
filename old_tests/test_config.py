import unittest
from unittest.mock import Mock, patch, mock_open
import yaml
import os
from producer_consumer.config import Config


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
            }
        }
        mock_yaml_load.return_value = incomplete_config
        config = Config('dummy_path.yaml')

        with self.assertRaises(KeyError):
            _ = config.produce_interval

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_config_invalid_values(self, mock_yaml_load, mock_file):
        invalid_config = {
            'producer': {
                'count': -1,  # Invalid negative value
                'produce_interval': 0,  # Invalid zero interval
                'start_urls': []  # Empty URL list
            },
            'consumer': {
                'count': 0,  # Invalid zero count
                'consume_interval': -1,  # Invalid negative interval
                'output_dir': ''  # Empty output directory
            },
            'queue': {
                'max_size': -100  # Invalid negative queue size
            },
            'logging': {
                'level': 'INVALID_LEVEL',
                'file': ''
            }
        }
        mock_yaml_load.return_value = invalid_config
        config = Config('dummy_path.yaml')

        # Test that invalid values are caught
        self.assertLess(config.producer_count, 1)
        self.assertLessEqual(config.produce_interval, 0)
        self.assertEqual(len(config.start_urls), 0)
        self.assertLessEqual(config.consumer_count, 0)
        self.assertLess(config.consume_interval, 0)
        self.assertEqual(config.output_dir, '')
        self.assertLess(config.queue_max_size, 0)

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_config_type_validation(self, mock_yaml_load, mock_file):
        invalid_type_config = {
            'producer': {
                'count': '2',  # String instead of int
                'produce_interval': '1.0',  # String instead of float
                'start_urls': 'http://test.com'  # String instead of list
            },
            'consumer': {
                'count': 3.5,  # Float instead of int
                'consume_interval': True,  # Bool instead of float
                'output_dir': 123  # Int instead of string
            },
            'queue': {
                'max_size': '100'  # String instead of int
            },
            'logging': {
                'level': 123,  # Int instead of string
                'file': True  # Bool instead of string
            }
        }
        mock_yaml_load.return_value = invalid_type_config
        config = Config('dummy_path.yaml')

        # Test type conversion handling
        with self.assertRaises((ValueError, TypeError, AttributeError)):
            _ = config.producer_count
            _ = config.produce_interval
            _ = config.start_urls
            _ = config.consumer_count
            _ = config.consume_interval
            _ = config.output_dir
            _ = config.queue_max_size
            _ = config.logging_level
            _ = config.logging_file

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_config_empty_file(self, mock_yaml_load, mock_file):
        mock_yaml_load.return_value = None
        with self.assertRaises(AttributeError):
            config = Config('dummy_path.yaml')

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_config_invalid_yaml(self, mock_yaml_load, mock_file):
        mock_yaml_load.side_effect = yaml.YAMLError
        with self.assertRaises(yaml.YAMLError):
            config = Config('dummy_path.yaml')


if __name__ == '__main__':
    unittest.main()