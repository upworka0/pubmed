#!/usr/bin/env python
import requests
from bs4 import BeautifulSoup
import re
import pandas
from pandas.io.excel import ExcelWriter
import os
import csv
import time
from dotenv import load_dotenv
from multiprocessing import Process, Manager
import math
from werkzeug.utils import secure_filename
from utils import write_csv, excel_out, get_thread_range


load_dotenv()

API_KEY = os.environ.get('API_KEY')
PREMIUM_PROXY = os.environ.get('PREMIUM_PROXY')
GENERAL_PROXY = os.environ.get('GENERAL_PROXY')
CREDENTIAL = os.environ.get('CREDENTIAL')
NCT_COUNT = 500

"""
Scraping module extended with Clinical NCT numbers
It is using for /clinical_scrap route in application
"""


class ScrapingUnit:
    """Scraping Unit"""
    def __init__(self, nct_records=None, page_number=1, csrfmiddlewaretoken="", session=None):
        self.nct_records = nct_records
        self.base_url = "https://pubmed.ncbi.nlm.nih.gov/"
        self.csrfmiddlewaretoken = csrfmiddlewaretoken
        self.total_count = 0
        self.nct = ''
        self.page_number = page_number
        self.results_dict = []
        self.results = []
        self.premium_proxy = {
            'http': 'http://{}@{}'.format(CREDENTIAL, PREMIUM_PROXY),
            'https': 'https://{}@{}'.format(CREDENTIAL, PREMIUM_PROXY)
        }
        self.general_proxy = {
            'http': 'http://{}@{}'.format(CREDENTIAL, GENERAL_PROXY),
            'https': 'https://{}@{}'.format(CREDENTIAL, GENERAL_PROXY)
        }

        if session is None:
            self.session = requests.session()
            headers = {
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
            }

            while True:
                try:
                    res = self.session.get(self.base_url, headers=headers)
                    soup = self.get_soup(res)
                    self.get_middleware_token(soup)
                    break
                except Exception as e:
                    print(e)
                    continue

        else:
            self.session = session
        self.count = 0

    def get_soup(self, response):
        """
        Return soup object from http response
        :param response
        :return: BeautifulSoup4 object
        """
        return BeautifulSoup(response.text, "html.parser")

    def get_middleware_token(self, soup):
        """
        Get csrfmiddlewaretoken from Soup
        :param soup
        :return: None
        """
        try:
            self.csrfmiddlewaretoken = soup.find('input', {'name': 'csrfmiddlewaretoken'}).attrs['value']
        except Exception as e:
            print(e)

    def get_total_count(self, soup):
        """
        Get Total count of search results
        :param soup
        :return: None
        """
        try:
            results_text = soup.find(attrs={'class': 'results-amount'}).text
            if 'No' in results_text:
                self.total_count = 0
            else:
                self.total_count = int(results_text.replace('results', '').replace(',', '').strip())
        except Exception as ex:
            print(type(ex).__name__, ex.args)
            self.total_count = 1

    def get_text(self, soup, ele, condition):
        """
        Get Text of Element from soup by condition
        :param soup
        :param ele
        :param condition
        :return: string
        """
        try:
            return soup.find(ele, condition).text.strip()
        except Exception as e:
            pass
        return ""

    def ajdust_abstract(self, abstract):
        """
        Remove unnecessary blanks and paragraphs
        :param abstract
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
        :param article
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
        """Return date of Absctact"""
        text = self.get_text(full_view, 'span', {"class": "cit"})
        return text.split(";")[0]

    def get_cond_inter_out(self, condition):
        """Get Conditions from Html content"""
        conditions = ''
        condition_soup = BeautifulSoup(condition, 'html.parser')
        lis = condition_soup.find_all('li')
        for li in lis:
            if conditions == '':
                conditions += li.text.replace('\n', '').strip()
            else:
                conditions += ' | {}'.format(li.text.replace('\n', '').strip())
        return conditions

    def get_header_information(self, article):
        """
        Return title, DOI, link, author names, abstract, affiliation and author email
        :param article
        :return: dict
        """
        # full_view = article.find('div', {'class': 'full-view'})
        full_view = article
        heading_title = self.get_text(full_view, 'h1', {'class': 'heading-title'})
        doi = self.get_text(full_view, 'span', {'class': 'citation-doi'}).strip('doi:')
        pmid = self.get_text(full_view, 'strong', {'class': 'current-id'})
        pmcid = self.get_text(full_view, 'span', {'class': 'identifier pmc'}).strip("PMCID:").strip()
        if pmcid == '':
            pmcid = self.get_text(full_view, 'span', {'class': 'identifier pubmed'}).strip("PMCID:").strip()
        date = self.get_date(full_view)
        authors_list = ''
        authors_spans = full_view.find_all('span', {'class': 'authors-list-item'})
        for author_span in authors_spans:
            name = self.get_text(author_span, 'a', {'class': 'full-name'})
            if authors_list == '':
                authors_list += name
            else:
                authors_list += ' | {}'.format(name)

        abstract = self.get_text(article, 'div', {'class': 'abstract-content selected'}).replace('\n', ' ')
        abstract = self.ajdust_abstract(abstract)

        affiliation, author_email = self.get_affiliations(article)

        return {
            "Pubmed link": "%s%s".strip() % (self.base_url, pmid),
            "heading_title": heading_title,
            "date": date,
            "abstract": abstract,
            "authors_list": authors_list,
            "affiliation": affiliation,
            "author_email": "|".join(author_email),
            "pmcid": pmcid,
            "doi": doi,
        }

    def get_full_text_links(self, article):
        """
        Return full text links from soup
        :param article
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
        :param article
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
        :param article
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

    def get_NCT(self, article):
        article_text = article.text
        for nct in self.nct_records:
            if nct[1] in article_text:
                return nct

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
            infor['full_text_links'] = " | ".join(self.get_full_text_links(article))
            infor['mesh_terms'] = " | ".join(self.get_mesh_terms(article))
            infor['publication_types'] = " | ".join(self.get_publication_types(article))
            infor['nct_number'] = self.get_NCT(article)
            if infor['nct_number'] is not None:
                infor['nct_number'] = infor['nct_number'][1]
            else:
                continue
            infor['conditions'] = self.get_cond_inter_out(self.get_NCT(article)[4])
            infor['interventions'] = self.get_cond_inter_out(self.get_NCT(article)[5])
            infor['outcome_measures'] = self.get_cond_inter_out(self.get_NCT(article)[11]).replace('●', '').strip()
            results_data.append(infor)
            self.count += 1

        lines = []
        for row in results_data:
            lines.append(list(row.values()))

        self.results_dict += results_data
        self.results += lines

    def unique_soup(self, soup):
        results_data = []
        infor = self.get_header_information(soup)
        infor['full_text_links'] = " | ".join(self.get_full_text_links(soup))
        infor['mesh_terms'] = " | ".join(self.get_mesh_terms(soup))
        infor['publication_types'] = " | ".join(self.get_publication_types(soup))
        infor['nct_number'] = self.get_NCT(soup)[1]
        infor['conditions'] = self.get_cond_inter_out(self.get_NCT(soup)[4])
        infor['interventions'] = self.get_cond_inter_out(self.get_NCT(soup)[5])
        infor['outcome_measures'] = self.get_cond_inter_out(self.get_NCT(soup)[11]).replace('●', '').strip()
        results_data.append(infor)
        self.count += 1

        lines = []
        for row in results_data:
            lines.append(list(row.values()))

        self.results_dict += results_data
        self.results += lines

    def next_page(self, keyword):
        """
            Scrap Next page
        """

        print("Scraping is starting in page %s" % self.page_number)

        url = "%smore/" % self.base_url
        milliseconds = int(round(time.time() * 1000))
        data = {
            "term": keyword,
            "size": 200,
            "page": self.page_number,
            "no_cache": "yes",
            "no-cache": milliseconds,
            "csrfmiddlewaretoken": self.csrfmiddlewaretoken,
            "format": "abstract"
        }

        headers = {
            "referer": "https://pubmed.ncbi.nlm.nih.gov/?term=%s&size=200&pos=%s" % (keyword, self.page_number - 1),
            "origin": "https://pubmed.ncbi.nlm.nih.gov",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
        }
        res = None
        while res is None:
            try:
                res = self.session.post(url=url, data=data, headers=headers, timeout=60)
            except Exception as e:
                print(e, self.page_number)

        soup = self.get_soup(res)
        self.get_middleware_token(soup)
        self.parse_soup(soup)

        if self.total_count > self.page_number * 200:
            self.page_number += 1
            return self.next_page(keyword=keyword)
        return None

    def do_scraping(self, keyword=None):
        print("Scraping is starting in page %s" % self.page_number)

        if self.page_number < 2:
            data = {
                "term": keyword,
                "size": 200,
                "format": "abstract",
            }
            headers = {
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36"
            }

            while True:
                try:
                    res = self.session.get(self.base_url, params=data, headers=headers)
                    if res.status_code != requests.codes.ok:
                        return None
                    soup = self.get_soup(res)
                    self.get_middleware_token(soup)
                    self.get_total_count(soup)
                    if self.total_count == 0:
                        return None
                    if self.total_count == 1:
                        self.unique_soup(soup)
                    else:
                        self.parse_soup(soup)
                    break
                except Exception as e:
                    print(e)
                    continue
            if self.total_count > self.page_number * 200:
                self.page_number += 1
                return self.do_scraping(keyword=keyword)
            return None
        else:
            self.next_page(keyword=keyword)
        print("Scraping was ended for page %s" % self.page_number)


class MultiThread(Process):
    """
        Threading module
        """
    def __init__(self, nct_records, csrfmiddlewaretoken, _range, session, results, results_dict):
        super(MultiThread, self).__init__()
        self._range = _range
        self.nct_records = nct_records
        self._rearrange = []
        self.csrfmiddlewaretoken = csrfmiddlewaretoken
        self.session = session
        self.results = results
        self.results_dict = results_dict

    def make_rearrange(self):
        count = len(self._range)  # NCT_COUNT + 1
        for i in range(count):
            item = []
            if i == count-1:
                for j in range(i*NCT_COUNT, len(self._range)):
                    item.append(self._range[j])
            else:
                for j in range(i*NCT_COUNT, (i+1)*NCT_COUNT):
                    item.append(self._range[j])
            self._rearrange.append(item)

    def make_query(self, _ran):
        query = '('
        for i in _ran:
            query += ') OR (' + self.nct_records[i][1]

        return query[5:] + """)) 
                AND ((clinicalstudy[Filter] OR clinicaltrial[Filter] OR clinicaltrialphasei[Filter] OR 
                clinicaltrialphaseii[Filter] OR clinicaltrialphaseiii[Filter] OR clinicaltrialphaseiv[Filter] 
                OR controlledclinicaltrial[Filter] OR pragmaticclinicaltrial[Filter]) AND (fft[Filter]))"""

    def run(self):
        self.make_rearrange()
        unit = ScrapingUnit(nct_records=self.nct_records, csrfmiddlewaretoken=self.csrfmiddlewaretoken)
        for _ran in self._rearrange:
            unit.do_scraping(keyword=self.make_query(_ran))
            if len(unit.results) > 0:
                print("Before", len(self.results), len(self.results_dict))
                self.results += unit.results
                self.results_dict += unit.results_dict
                print("After", len(self.results), len(self.results_dict))


def Pubmed_Job(keyword, numbers, result_folder):
    """
    Scraping module extended with Clinical NCT numbers
    """
    dir_name = os.path.dirname(__file__)

    manager = Manager()
    results = manager.list()
    results_dict = manager.list()

    results.append([
        "Pubmed link", "Title", "Date", "Abstract", "Authors", "Author affiliation", "Author email", "PMCID", "DOI",
        "Full text link", "Mesh terms", "Publication type", "NCT number", "Conditions", "Interventions",
        "Outcome measures"
    ])

    unit = ScrapingUnit()
    session = unit.session
    csrfmiddlewaretoken = unit.csrfmiddlewaretoken

    threads = []
    # Thread count
    thread_count = 5
    ranges = get_thread_range(thread_count=thread_count, total_count=math.ceil(len(numbers)))

    for _range in ranges:
        thread = MultiThread(
            nct_records=numbers,
            csrfmiddlewaretoken=csrfmiddlewaretoken,
            _range=_range,
            session=session,
            results=results,
            results_dict=results_dict
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    keyword = '{} {}'.format(keyword['conditions_disease'], keyword['other_terms'])

    file_name = secure_filename(keyword)
    file_name = file_name[:200]

    csv_file = os.path.join(dir_name, result_folder, "%s.csv" % file_name)
    write_csv(csv_file, results[:])

    excel_relational_path = os.path.join(result_folder, "%s.xlsx" % file_name)
    excel_absolute_path = os.path.join(dir_name, excel_relational_path)
    excel_out(csv_file, excel_absolute_path)
    return results_dict[:], excel_relational_path, file_name
