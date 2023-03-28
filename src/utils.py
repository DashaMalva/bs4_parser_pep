import logging

from bs4 import BeautifulSoup
from requests import RequestException

from exceptions import ParserFindTagException


def get_response(session, url):
    """Проверяет доступность url-адреса.

    Parameters:
    session - инициализированная сессия для работы с сайтом.
    url - проверяемый абсолютный url-адрес.
    Returns:
    В случае доступность url возвращает ответ сервера.
    """
    try:
        response = session.get(url)
        response.encoding = 'utf-8'
        return response
    except RequestException:
        logging.exception(
            f'Возникла ошибка при загрузке страницы {url}',
            stack_info=True
        )


def find_tag(soup, tag: str, attrs=None):
    """Проверяет, что искомый тег существует.

    Parameters:
    soup - объект класса BeautifulSoup, в котором ищется тег.
    tag - искомый тег.
    attrs(необязательный параметр) - словарь с атрибутами тега.
    Returns:
    Возвращает искомый тег либо выбрасывает исключение.
    """
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        error_msg = f'Не найден тег {tag} {attrs}'
        logging.error(error_msg, stack_info=True)
        raise ParserFindTagException(error_msg)
    return searched_tag


def get_pep_status_list(soup) -> list:
    """Парсит переданную страницу и возращает список возможных статусов PEP.

    Parameters:
    soup - объект класса BeautifulSoup, в котором ищутся статусы.
    Returns:
    (list[str]) список статусов.
    """
    status_section = find_tag(
        soup, 'section', attrs={'id': 'pep-status-key'})
    status_ul_tag = find_tag(
        status_section, 'ul', attrs={'class': 'simple'})
    status_tags = status_ul_tag.find_all('em')
    statuses = [status.text for status in status_tags]
    return statuses


def get_pep_page_status(session, link: str) -> str:
    """Парсит страницу PEP и возвращает его статус.

    Parameters:
    session - инициализированная сессия для работы с сайтом.
    link (str) - абсолютная ссылка на страницу PEP.
    Returns:
    (str) статус PEP.
    """
    response = get_response(session, link)
    if response is None:
        logging.info(f'Не получилось перейти по ссылке {link}')
        return
    soup = BeautifulSoup(response.text, features='lxml')
    pep_content_section = find_tag(
        soup, 'section', attrs={'id': 'pep-content'})
    desctiption_tag = find_tag(pep_content_section, 'dl')
    desctiption_details = desctiption_tag.find_all('dt')
    for detail in desctiption_details:
        if 'Status' in detail.text:
            status_tag = detail.find_next_sibling()
            return status_tag.text
    logging.info(f'Статус не обнаружен {link}')
