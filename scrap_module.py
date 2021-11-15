#!/usr/bin/env python
"""
    Scraping module for only pumbed
"""
import requests
from bs4 import BeautifulSoup
import time
import re
import pandas
from pandas.io.excel import ExcelWriter
import os
import csv
from multiprocessing import Process, Manager
import math
from werkzeug.utils import secure_filename
from utils import write_csv, excel_out, get_thread_range_pumbed


class ScrapingUnit:
    """
        Scraping Unit
        """

    def __init__(self, keyword, csrfmiddlewaretoken="", page_number=1, session=None):
        self.keyword = keyword
        self.base_url = "https://pubmed.ncbi.nlm.nih.gov/"
        self.csrfmiddlewaretoken = csrfmiddlewaretoken
        self.page_number = page_number
        self.total_count = 0
        self.results_dict = []
        self.results = []

        if session is None:
            self.session = requests.session()
            headers = {
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
            }

            res = self.session.get(self.base_url, headers=headers)
            soup = self.get_soup(res)
            self.get_middleware_token(soup)
        else:
            self.session = session
        self.count = 0

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
        try:
            self.csrfmiddlewaretoken = soup.find('input', {'name': 'csrfmiddlewaretoken'}).attrs['value']
        except Exception as e:
            print(e, self.page_number)

    def get_total_count(self, soup):
        """
            Get Total count of search results
        :param soup:
        :return: None
        """
        if soup.find('div', {'class': 'results-amount'}):
            self.total_count = int(soup.find('div', {'class': 'results-amount'}).
                               text.strip().replace('results', '').replace(',', '').strip())
        else:
            self.total_count = 0

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
        author_email = []
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
                    for email in lst:
                        author_email.append(email.strip().strip(",").strip(".").strip(";"))
                        text = text.replace(email, '').strip()

                    affiliation = text.replace("Electronic address:", "").replace("Electronic address", '')\
                        .strip().strip(",").strip(".").strip(";")

        return affiliation, author_email

    def get_date(self, full_view):
        """
            Return date of Absctact
            """
        text = self.get_text(full_view, 'span', {"class": "cit"})
        return text.split(";")[0]

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
        date = self.get_date(full_view)
        authors_list = []
        authors_spans = full_view.find_all('span', {'class': 'authors-list-item'})
        for author_span in authors_spans:
            name = self.get_text(author_span, 'a', {'class': 'full-name'})
            authors_list.append(name)

        abstract = self.get_text(article, 'div', {'class': 'abstract-content selected'}).replace('\n\n', '')
        abstract = self.ajdust_abstract(abstract)

        affiliation, author_email = self.get_affiliations(article)

        return {
            "Pubmed link": "%s%s" % (self.base_url, pmid),
            "heading_title": heading_title,
            "date": date,
            "abstract": abstract,
            "authors_list": ", \n".join(authors_list),
            "affiliation": affiliation,
            "author_email": ", \n".join(author_email),
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
        results_data = []
        for article in articles_div:
            infor = self.get_header_information(article)
            infor['full_text_links'] = ",\n".join(self.get_full_text_links(article))
            infor['mesh_terms'] = ", \n".join(self.get_mesh_terms(article))
            infor['publication_types'] = ", \n".join(self.get_publication_types(article))
            results_data.append(infor)
            self.count += 1

        lines = []
        for row in results_data:
            lines.append(list(row.values()))

        self.results_dict += results_data
        self.results += lines

    def next_page(self):
        """
            Scrap Next page
        """

        print("Scraping is starting in page %s" % self.page_number)

        url = "%smore/" % self.base_url
        milliseconds = int(round(time.time() * 1000))
        data = {
            "term": self.keyword,
            "size": 100,
            "page": self.page_number,
            "no_cache": "yes",
            "no-cache": milliseconds,
            "csrfmiddlewaretoken": self.csrfmiddlewaretoken,
            "format": "abstract"
        }

        headers = {
            "referer": "https://pubmed.ncbi.nlm.nih.gov/?term=%s&size=100&pos=%s" % (self.keyword, self.page_number - 1),
            "origin": "https://pubmed.ncbi.nlm.nih.gov",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
        }
        res = None
        while res is None:
            try:
                res = self.session.post(url=url, data=data, headers=headers, timeout=60)
                time.sleep(1)
            except Exception as e:
                print(e, self.page_number)
                time.sleep(1)

        soup = self.get_soup(res)
        self.get_middleware_token(soup)
        self.parse_soup(soup)

    def do_scraping(self):
        if self.page_number < 2:
            print("Scraping is starting in page %s" % self.page_number)
            data = {
                "term": self.keyword,
                "size": 100,
                "format": "abstract"
            }
            headers = {
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36"
            }

            res = self.session.get(self.base_url, params=data, headers=headers)
            print(res.status_code)
            soup = self.get_soup(res)
            self.get_middleware_token(soup)
            self.get_total_count(soup)
            print(self.total_count)
            self.parse_soup(soup)
        else:
            self.next_page()
            # print(self.results_dict)

        print("Scraping was ended for page %s" % self.page_number)


class MultiThread(Process):
    """
        Threading module
        """
    def __init__(self, keyword, csrfmiddlewaretoken, page_range, session, results, results_dict):
        super(MultiThread, self).__init__()
        self.page_range = page_range
        self.keyword = keyword
        self.csrfmiddlewaretoken = csrfmiddlewaretoken
        self.session = session
        self.results = results
        self.results_dict = results_dict

    def run(self):
        print(self.page_range)
        for page_number in self.page_range:
            unit = ScrapingUnit(keyword=self.keyword,
                                csrfmiddlewaretoken=self.csrfmiddlewaretoken,
                                page_number=page_number)
            while True:
                unit.do_scraping()
                if len(unit.results) > 0:
                    print("Before", page_number, len(self.results), len(self.results_dict))
                    self.results += unit.results
                    self.results_dict += unit.results_dict
                    print("After", page_number, len(self.results), len(self.results_dict))
                    break


def Scraping_Job(keyword, result_folder):
    dirname = os.path.dirname(__file__)

    manager = Manager()
    results = manager.list()
    results_dict = manager.list()

    results.append([
        "Pubmed link", "Title", "Date", "Abstract", "Authors", "Author affiliation", "Author email", "PMCID", "DOI",
        "Full text link", "Mesh terms", "Publication type"
    ])

    total_count = 0
    unit = ScrapingUnit(keyword=keyword)
    unit.do_scraping()
    session = unit.session

    results += unit.results
    results_dict += unit.results_dict
    total_count += unit.total_count
    csrfmiddlewaretoken = unit.csrfmiddlewaretoken

    threads = []
    # Thread count
    thread_count = 4
    ranges = get_thread_range_pumbed(thread_count=thread_count, total_count=math.ceil(total_count/100))

    for page_range in ranges:
        thread = MultiThread(
            keyword=keyword,
            csrfmiddlewaretoken=csrfmiddlewaretoken,
            page_range=page_range,
            session=session,
            results=results,
            results_dict=results_dict
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    file_name = secure_filename(keyword)
    file_name = file_name[:200]

    csv_file = os.path.join(dirname, result_folder, "%s.csv" % file_name)
    write_csv(csv_file, results[:])

    excel_relational_path = os.path.join(result_folder, "%s.xlsx" % file_name)
    excel_absolute_path = os.path.join(dirname, excel_relational_path)
    excel_out(csv_file, excel_absolute_path)
    return results_dict[:], excel_relational_path, file_name
