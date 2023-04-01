import logging
import re
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, MAIN_DOC_URL, PEP_URL, STATUS_MATCH_MSG_PATTERN
from outputs import control_output
from utils import (get_response, get_pep_page_status, get_pep_status_list,
                   find_tag)


def whats_new(session) -> list[tuple]:
    """Парсер статей о нововведениях в Python.

    Parameters:
    session - инициализированная сессия для работы с сайтом.
    Returns:
    (list[tuple]) результат парсинга в виде списка кортежей, где первый элемент
    - ссылка на статью, второй - заголовок, третий - редактор/автор.
    """
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    main_div = find_tag(
        soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(
        main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'})

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for section in tqdm(sections_by_python, desc='What\'s new'):
        version_a_tag = section.find('a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, features='lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append((version_link, h1.text, dl_text))
    return results


def latest_versions(session) -> list[tuple]:
    """Парсер информации о версиях Python.

    Parameters:
    session - инициализированная сессия для работы с сайтом.
    Returns:
    (list[tuple]) результат парсинга в виде списка кортежей, где первый элемент
    - ссылка на документацию, второй - версия Python, третий - статус.
    """
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    sidebar = find_tag(
        soup, 'div', {'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')

    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise Exception('Не найден список c версиями Python')

    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a in a_tags:
        text_match = re.search(pattern, a.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a.text, ''
        results.append((a['href'], version, status))
    return results


def download(session) -> None:
    """Скачивает zip архив с актуальной документацией Python в формате pdf.

    Parameters:
    session - инициализированная сессия для работы с сайтом.
    """
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    main_div = find_tag(soup, 'div', {'role': 'main'})
    table_tag = find_tag(main_div, 'table', {'class': 'docutils'})
    pdf_a4_tag = find_tag(
        table_tag, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')})
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)

    filename = pdf_a4_link.split('/')[-1]
    download_dir = BASE_DIR / 'downloads'
    download_dir.mkdir(exist_ok=True)
    archive_path = download_dir / filename

    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session) -> list[tuple]:
    """Парсер статусов документов PEP.

    Parameters:
    session - инициализированная сессия для работы с сайтом.
    Returns:
    (list[tuple]) результат парсинга в виде списка кортежей, где первый элемент
    - статус PEP, второй - количество PEP данного статуса.
    """
    response = get_response(session, PEP_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')

    pep_amount = 0
    status_list = get_pep_status_list(soup)
    status_amount = dict.fromkeys(status_list, 0)
    status_match_info = []

    status_section = find_tag(
        soup, 'section', attrs={'id': 'numerical-index'})
    status_table = find_tag(status_section, 'tbody')
    status_table_rows = status_table.find_all('tr')

    for row in tqdm(status_table_rows, desc='PEP status'):
        pep_amount += 1
        status_tag = find_tag(row, 'abbr')
        card_status = status_tag['title'].split()[-1]
        link_tag = find_tag(row, 'a')
        pep_page_link = urljoin(PEP_URL, link_tag['href'])
        pep_page_status = get_pep_page_status(
            session, pep_page_link)
        if pep_page_status in status_list:
            status_amount[pep_page_status] += 1
        else:
            logging.info(f'Статус {pep_page_status} отсутствует в списке '
                         f'статусов {status_list} {pep_page_link}')
        if card_status != pep_page_status:
            status_match_info.append(STATUS_MATCH_MSG_PATTERN.format(
                link=pep_page_link,
                card_status=card_status,
                page_status=pep_page_status
            ))
    if status_match_info:
        status_match_info.append('Несовпадающие статусы\n')
        logging.info(*status_match_info)
    results = [('Статус', 'Количество')]
    results.extend(status_amount.items())
    results.append(('Total', pep_amount))
    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)
    if results is not None:
        control_output(results, args)
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
