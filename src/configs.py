import argparse
import logging
from logging.handlers import RotatingFileHandler

from constants import BASE_DIR


LOG_FORMAT = '"%(asctime)s - [%(levelname)s] - %(message)s"'
DT_FORMAT = '%d.%m.%Y %H:%M:%S'


def configure_argument_parser(available_modes):
    """Настройка парсера аргументов командной строки.

    Parameters:
    available_modes (list) - список режимов работы парсера.
    """
    parser = argparse.ArgumentParser(description='Парсер документации Python')
    parser.add_argument(
        'mode',
        choices=available_modes,
        help='Режимы работы парсера'
    )
    parser.add_argument(
        '-c',
        '--clear-cache',
        action='store_true',
        help='Очистка кеша'
    )
    parser.add_argument(
        '-o',
        '--output',
        choices=('pretty', 'file'),
        help='Дополнительные способы вывода данных'
    )
    return parser


def configure_logging():
    """Настройка логирования проекта."""
    log_dir = BASE_DIR / 'logs'
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / 'parser.log'
    rotating_handler = RotatingFileHandler(
        log_file, maxBytes=10 ** 6, backupCount=5, encoding='utf-8'
    )
    logging.basicConfig(
        level=logging.INFO,
        datefmt=DT_FORMAT,
        format=LOG_FORMAT,
        encoding='utf-8',
        handlers=(rotating_handler, logging.StreamHandler())
    )
