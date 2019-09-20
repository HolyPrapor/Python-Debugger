#!/usr/bin/env python3
# coding=utf-8
import re
from urllib.request import urlopen
from urllib.parse import quote, unquote
from urllib.error import URLError, HTTPError
from difflib import SequenceMatcher


def count_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


def get_content(name):
    try:
        with urlopen('http://ru.wikipedia.org/wiki/' + quote(name)) as page:
            content = page.read().decode('utf-8', errors='ignore')
    except (URLError, HTTPError):
        return False
    return content


def extract_content(page):
    if not page:
        return None
    start_index = re.search('mw-content-text', page).start()
    end_index = re.search('class="printfooter"', page).start()
    if start_index < 0 or end_index < 0:
        return 0, 0
    return start_index, end_index


const_filters = [re.compile("Шаблон:"), re.compile("Википедия:"),
                 re.compile("Служебная:"), re.compile("Файл:"),
                 re.compile("Категория:"), re.compile("Участник:")]


def extract_links(page, begin, end):
    links = map(unquote,
                re.findall(
                    r'<a\s+href=["\']/wiki/(?!category)(?!C:)([^"#]+?)["\']',
                    page[begin:end], flags=re.IGNORECASE))
    answer = set()
    for link in links:
        has_match = False
        for filter in const_filters:
            if filter.search(link):
                has_match = True
                break
        if not has_match:
            answer.add(link)
    return list(answer)


def make_step_back(trek_table, current_page):
    if len(trek_table) == 1 and current_page == start:
        return None
    elif len(trek_table) == 1:
        return start
    else:
        return trek_table.pop()


def find_chain(start, finish):
    trek_table = [start]
    visited_links = set()
    current_page = start
    while finish not in trek_table:
        content = get_content(current_page)
        if not content:
            current_page = make_step_back(trek_table, current_page)
            if current_page is None:
                return None
            continue
        content_start_index, content_finish_index = extract_content(content)
        links = \
            extract_links(content, content_start_index, content_finish_index)
        if finish in links:
            trek_table.append(finish)
            return trek_table
        sorted_links = \
            sorted(links, key=lambda x: count_similarity(finish, x),
                   reverse=True)
        next_link_exists = False
        for link in sorted_links:
            if link not in visited_links:
                trek_table.append(link)
                visited_links.add(link)
                current_page = link
                next_link_exists = True
                break
        if not next_link_exists:
            current_page = make_step_back(trek_table, current_page)
            if current_page is None:
                return None
    return trek_table


def main():
    print(find_chain("Россия", "Философия"))


if __name__ == '__main__':
    main()
