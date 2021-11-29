from bs4 import BeautifulSoup


def parse_soup(content):
    return BeautifulSoup(content, 'html.parser')