from pathlib import Path

BASE_DIR = Path(__file__).parent
DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
EXPECTED_STATUS = {}
MAIN_DOC_URL = 'https://docs.python.org/3/'
PEP_URL = 'https://peps.python.org/'
STATUS_MATCH_MSG_PATTERN = ('{link}\nСтатус в карточке: '
                            '{card_status}\nОжидаемые статусы: {page_status}')
