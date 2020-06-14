#!/usr/bin/env python
import requests
from bs4 import BeautifulSoup
import time
import re
import pandas
from pandas.io.excel import ExcelWriter
import os
import csv


class ScrapingUnit:
    """
        Scraping Unit
        """

    def __init__(self, keyword):
        self.base_url = "https://pubmed.ncbi.nlm.nih.gov/"
        self.csrfmiddlewaretoken = ""
        self.keyword = keyword
        self.session = requests.session()
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
        }
        self.session.get(self.base_url, headers=headers)
        self.total_count = 0
        self.count = 0
        self.results_dict = []

        self.results = [[
            "Pubmed link", "Title", "Abstract", "Authors", "Author email", "Author affiliation", "PMCID", "DOI",
            "Full text link", "Mesh terms", "Publication type"
        ]]

        self.csv_file = "static/downloads/%s.csv" % keyword
        self.excel_file = "static/downloads/%s.xlsx" % keyword

    def get_soup(self, response):
        """
            Return soup object from http response
        :param response:
        :return: BeautifulSoup4 object
        """
        return BeautifulSoup(response.text, "html.parser")

    def get_middleware_token(self, soup):
        """
            Get csrfmiddlewaretoken from Soup
        :param soup:
        :return: None
        """
        self.csrfmiddlewaretoken = soup.find('input', {'name': 'csrfmiddlewaretoken'}).attrs['value']

    def get_total_count(self, soup):
        """
            Get Total count of search results
        :param soup:
        :return: None
        """
        self.total_count = int(soup.find('div', {'class': 'results-amount'}).text.strip().replace('results', ''))

    def get_text(self, soup, ele, condition):
        """
        Get Text of Element from soup by condition
        :param soup:
        :param ele:
        :param condition:
        :return: string
        """
        try:
            return soup.find(ele, condition).text.strip()
        except Exception as e:
            # print(ele, condition)
            pass
        return ""

    def ajdust_abstract(self, abstract):
        """
        Remove unnecessary blanks and paragraphs
        :param abstract:
        :return: string
        """
        slices = abstract.split('\n')
        full_text = ""
        for i in range(len(slices) - 2):
            if slices[i + 1].strip() == '' and slices[i + 2].strip() == '':
                full_text += slices[i].strip() + '\n\n'
                i += 2
        full_text += slices[len(slices) - 1].strip()
        return full_text

    def get_affiliations(self, article):
        """
        Return affiliation and author email
        :param article:
        :return: string, string
        """
        affiliations_div = article.find('div', {'class': 'affiliations'})
        affiliation = ""
        author_email = ""
        if affiliations_div:
            first = True
            for li in affiliations_div.find_all('li'):
                sup_key = self.get_text(li, 'sup', {})
                text = li.text.strip()[len(sup_key):]
                if first:
                    affiliation = text
                    first = False

                lst = re.findall('\S+@\S+', text)
                if len(lst) > 0:
                    author_email = lst[0]
                    affiliation = text.strip(author_email).strip("Electronic address").strip("Electronic address:")
                    author_email = author_email.strip(".")

        return affiliation, author_email

    def get_header_information(self, article):
        """
        Return title, DOI, link, author names, abstract, affiliation and author email
        :param article:
        :return: dict
        """
        full_view = article.find('div', {'class': 'full-view'})
        heading_title = self.get_text(full_view, 'h1', {'class': 'heading-title'})
        doi = self.get_text(full_view, 'span', {'class': 'citation-doi'}).strip('doi:')
        pmid = self.get_text(full_view, 'strong', {'class': 'current-id'})
        pmcid = self.get_text(full_view, 'span', {'class': 'identifier pmc'}).strip("PMCID:").strip()
        authors_list = []
        authors_spans = article.find_all('span', {'class': 'authors-list-item'})
        for author_span in authors_spans:
            name = self.get_text(author_span, '', {'class': 'full-name'})
            authors_list.append(name)

        abstract = self.get_text(article, 'div', {'class': 'abstract-content selected'}).replace('\n\n', '')
        abstract = self.ajdust_abstract(abstract)

        affiliation, author_email = self.get_affiliations(article)

        return {
            "Pubmed link": "%s%s" % (self.base_url, pmid),
            "heading_title": heading_title,
            "abstract": abstract,
            "authors_list": ", ".join(authors_list),
            "affiliation": affiliation,
            "author_email": author_email,
            "pmcid": pmcid,
            "doi": doi,
        }

    def get_full_text_links(self, article):
        """
        Return full text links from soup
        :param article:
        :return: array
        """
        full_text_links = []
        full_text_links_list_div = article.find('div', {'class': 'full-text-links-list'})
        if full_text_links_list_div:
            atags = full_text_links_list_div.find_all('a')
            for tag in atags:
                full_text_links.append(tag.attrs['href'])

        return full_text_links

    def get_mesh_terms(self, article):
        """
        Return array of mesh terms from soup
        :param article:
        :return: array
        """
        mesh_terms = []
        mesh_div = article.find('div', {'class': 'mesh-terms keywords-section'})
        if mesh_div:
            keyword_list = mesh_div.find('ul', {'class': 'keywords-list'})
            if keyword_list:
                for button in keyword_list.find_all('button', {'class': 'keyword-actions-trigger'}):
                    mesh_terms.append(button.text.strip())
        return mesh_terms

    def get_publication_types(self, article):
        """
        Return publication types from soup
        :param article:
        :return: array
        """
        pub_types = []
        pub_types_div = article.select('div[class*="publication-types keywords-section"]')
        if len(pub_types_div) > 0:
            keyword_list = pub_types_div[0].find('ul', {'class': 'keywords-list'})
            if keyword_list:
                for button in keyword_list.find_all('button', {'class': 'keyword-actions-trigger'}):
                    pub_types.append(button.text.strip())
        return pub_types

    def parse_soup(self, soup):
        """
        Parse soup object to get necessary information
        :param soup: BeautifulSoup4 Object
        :return: None
        """
        articles_div = soup.find_all('div', {"class": "results-article"})
        results = []
        for article in articles_div:
            infor = self.get_header_information(article)
            infor['full_text_links'] = ", ".join(self.get_full_text_links(article))
            infor['mesh_terms'] = ", ".join(self.get_mesh_terms(article))
            infor['publication_types'] = ", ".join(self.get_publication_types(article))
            results.append(infor)
            self.count += 1

        lines = []
        for row in results:
            lines.append(list(row.values()))

        self.results_dict = self.results_dict + results
        self.results = self.results + lines

    def next_page(self, page_number):
        """
            Scrap Next page
        """
        url = "%smore/" % self.base_url
        milliseconds = int(round(time.time() * 1000))
        data = {
            "term": self.keyword,
            "size": 200,
            "page": page_number,
            "no_cache": "yes",
            "no-cache": milliseconds,
            "csrfmiddlewaretoken": self.csrfmiddlewaretoken,
            "format": "abstract"
        }

        headers = {
            "referer": "https://pubmed.ncbi.nlm.nih.gov/?term=%s&size=200&pos=%s" % (self.keyword, page_number - 1),
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
        }

        res = self.session.post(url=url, data=data, headers=headers)
        soup = self.get_soup(res)
        print("Page %s" % page_number)
        self.parse_soup(soup)

        if self.total_count > self.count:
            self.next_page(page_number + 1)

    def write_csv(self):
        """
        Write lines to csv named as filename
        """
        with open(self.csv_file, 'w', encoding='utf-8', newline='') as writeFile:
            writer = csv.writer(writeFile, delimiter=',')
            writer.writerows(self.results)

    def excel_out(self):
        # convert csv file to excel format
        with ExcelWriter(self.excel_file) as ew:
            df = pandas.read_csv(self.csv_file)
            df.to_excel(ew, sheet_name="sheet1", index=False)

    def do_scraping(self):
        print("Scraping is starting ...")
        data = {
            "term": self.keyword,
            "size": 200,
            "format": "abstract"
        }
        print("Page 1")
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
        }
        res = self.session.get(self.base_url, params=data, headers=headers)
        soup = self.get_soup(res)
        self.get_middleware_token(soup)
        self.get_total_count(soup)
        self.parse_soup(soup)
        if self.total_count > self.count:
            self.next_page(2)
        self.write_csv()
        self.excel_out()

        print("Scraping was ended.")
        return self.results_dict, self.excel_file
