from .abstract import Site
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
from .exceptions import NoDownloadableContentFound, NoPDFLinkFound
import logging
import os
from .helpers import get_filename_from_cd, is_downloadable, retry


class NIHGov(Site):
    """
        Sample: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4628785/
    """
    def __init__(self, url, download_dir):
        super().__init__()
        self.url = url
        self.download_path = download_dir

        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
        }
        self.session = requests.session()
        self.session.headers.update(self.headers)

    def get_redirect_url(self):
        r = self.session.get(self.url, headers=self.headers, allow_redirects=False)
        return r.headers['Location']

    @retry(Exception, tries=5, delay=2)
    def get_page_source(self):
        return self.session.get(self.get_redirect_url(), headers=self.headers)

    def get_pdf_url(self):
        html = self.get_page_source().content
        soup = BeautifulSoup(html, "html.parser")
        elements = soup.find("div", class_="format-menu").find("ul").find_all("li")

        for element in elements:
            if ".pdf" in str(element):
                pdf_path = element.find("a")['href']
                parsed_url = urlparse(self.url)
                pdf_link = "{scheme}://{netloc}{path}".format(scheme=parsed_url.scheme,
                                                              netloc=parsed_url.netloc,
                                                              path=pdf_path)
                return pdf_link
        return False

    @retry(Exception, tries=3, delay=1)
    def download_pdf(self, url):
        downloadable = is_downloadable(self.session, url)
        if downloadable:
            r = self.session.get(url, allow_redirects=True)
            filename = get_filename_from_cd(r.headers.get('content-disposition'))
            full_path = os.path.join(self.download_path, filename)
            with open(full_path, 'wb') as writer:
                writer.write(r.content)
            logging.info("PDF Downloaded")
            return filename
        else:
            raise NoDownloadableContentFound

    def start_scrape(self):
        url = self.get_pdf_url()
        if not url:
            raise NoPDFLinkFound

        res = self.download_pdf(url)
        self.session.close()
        return res


class WhiteRose(Site):
    """
        Sample: http://eprints.whiterose.ac.uk/122838/
    """

    def __init__(self, url, download_dir):
        super().__init__()
        self.url = url
        self.download_path = download_dir

        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
        }
        self.session = requests.session()
        self.session.headers.update(self.headers)

    @retry(Exception, tries=5, delay=2)
    def get_page_source(self):
        return self.session.get(self.url, headers=self.headers)

    def get_pdf_url(self, **args):
        html = self.get_page_source().content
        soup = BeautifulSoup(html, "html.parser")
        elements = soup.find_all("a", href=True, text=re.compile("CLICK TO DOWNLOAD"))
        try:
            pdf_link = elements[-1]['href']
        except Exception:
            raise NoPDFLinkFound
        return pdf_link

    @retry(Exception, tries=3, delay=1)
    def download_pdf(self, url):
        downloadable = is_downloadable(self.session, url)
        if downloadable:
            r = self.session.get(url, allow_redirects=True)
            filename = get_filename_from_cd(r.headers.get('content-disposition'))
            full_path = os.path.join(self.download_path, filename)
            with open(full_path, 'wb') as writer:
                writer.write(r.content)
            logging.info("PDF Downloaded")
            return filename
        else:
            raise NoDownloadableContentFound

    def start_scrape(self):
        url = self.get_pdf_url()
        if not url:
            raise NoPDFLinkFound

        res = self.download_pdf(url)
        self.session.close()
        return res


class UnknownSite(Site):
    def __init__(self, url, download_dir):
        super().__init__()
        self.url = url
        self.download_path = download_dir

        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
        }
        self.session = requests.session()
        self.session.headers.update(self.headers)

    def get_page_source(self):
        return self.session.get(self.url, headers=self.headers)

    def get_pdf_url(self, **args):
        pass

    def download_pdf(self, **args):
        pass

    def start_scrape(self):
        pass
