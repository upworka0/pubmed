from .abstract import Site
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse
import re
from .exceptions import NoDownloadableContentFound, NoPDFLinkFound, CanNotGetPageSource, DownloadOperationException
import logging
import os
from .helpers import get_filename_from_cd, is_downloadable, retry, rename_file
from selenium import webdriver
from .webdriver_utils import get_driver_path
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path


driver_path = get_driver_path()
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--disable-software-rasterizer')
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--verbose')


class NIHGov(Site):
    """
        Sample: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4628785/
    """

    def __init__(self, url, download_dir, pdf_name):
        super().__init__()
        self.url = url
        self.download_path = download_dir
        self.pdf_name = pdf_name

        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
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
        raise NoPDFLinkFound

    @retry(Exception, tries=5, delay=2)
    def download_pdf(self, url):
        downloadable = is_downloadable(self.session, url)
        if downloadable:
            r = self.session.get(url, allow_redirects=True)
            # filename = get_filename_from_cd(r.headers.get('content-disposition'))
            filename = self.pdf_name
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

    def __init__(self, url, download_dir, pdf_name):
        super().__init__()
        self.url = url
        self.download_path = download_dir
        self.pdf_name = pdf_name

        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
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

    @retry(Exception, tries=5, delay=2)
    def download_pdf(self, url):
        downloadable = is_downloadable(self.session, url)
        if downloadable:
            r = self.session.get(url, allow_redirects=True)
            # filename = get_filename_from_cd(r.headers.get('content-disposition'))
            filename = self.pdf_name
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


class UnitoIt(Site):
    """
        Samples:
            https://iris.unito.it/handle/2318/1673185#.X7FAInUzaV7
            https://iris.unito.it/handle/2318/1636249#.X7FAInUzaV6
            https://iris.unito.it/handle/2318/1557489#.X7FAInUzaV5
    """

    def __init__(self, url, download_dir, pdf_name):
        super().__init__()
        self.url = url
        self.download_path = download_dir
        self.pdf_name = pdf_name

        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
        }
        self.session = requests.session()
        self.session.headers.update(self.headers)

    @retry(Exception, tries=5, delay=2)
    def get_page_source(self):
        return self.session.get(self.url, headers=self.headers)

    def get_pdf_url(self, **args):
        html = self.get_page_source().content
        soup = BeautifulSoup(html, "html.parser")
        elements = soup.find("table", class_="table panel-body").find("tr").find_next_siblings("tr")

        try:
            for element in elements:
                if "Open Access" in str(element):
                    href = element.find("td").find("a", href=True)['href']
                    parsed_url = urlparse(self.url)
                    root_url = "{scheme}://{netloc}".format(scheme=parsed_url.scheme,
                                                            netloc=parsed_url.netloc)
                    pdf_link = root_url + href
                    return pdf_link
        except Exception:
            raise NoPDFLinkFound

    @retry(Exception, tries=5, delay=2)
    def download_pdf(self, url):
        downloadable = is_downloadable(self.session, url)
        if downloadable:
            r = self.session.get(url, allow_redirects=True)
            # filename = get_filename_from_cd(r.headers.get('content-disposition'))
            filename = self.pdf_name
            full_path = os.path.join(self.download_path, filename)
            with open(full_path, 'wb') as writer:
                writer.write(r.content)
            logging.info("PDF Downloaded")
            return filename
        raise NoPDFLinkFound

    def start_scrape(self):
        url = self.get_pdf_url()
        if not url:
            raise NoPDFLinkFound
        res = self.download_pdf(url)
        self.session.close()
        return res


class OUP(Site):
    """
        Samples:
            https://academic.oup.com/jnen/article/77/7/608/4999948
            https://academic.oup.com/peds/article/30/6/431/3799720
    """
    def __init__(self, url, download_dir, pdf_name):
        super().__init__()
        self.url = url
        self.download_path = download_dir
        self.pdf_name = pdf_name

        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
        }
        self.session = requests.session()
        self.session.headers.update(self.headers)

    @retry(Exception, tries=5, delay=2)
    def get_page_source(self):
        return self.session.get(self.url, headers=self.headers)

    def get_pdf_url(self, **args):
        html = self.get_page_source().content
        soup = BeautifulSoup(html, "html.parser")
        pdf_href = soup.find("a", class_="al-link pdf article-pdfLink", href=True)['href']
        try:
            parsed_url = urlparse(self.url)
            root_url = "{scheme}://{netloc}".format(scheme=parsed_url.scheme,
                                                    netloc=parsed_url.netloc)
            pdf_link = root_url + pdf_href
            return pdf_link
        except Exception:
            raise NoPDFLinkFound

    @retry(Exception, tries=5, delay=2)
    def download_pdf(self, url):
        downloadable = is_downloadable(self.session, url)
        if downloadable:
            r = self.session.get(url, allow_redirects=True)
            filename = self.pdf_name
            full_path = os.path.join(self.download_path, filename)
            with open(full_path, 'wb') as writer:
                writer.write(r.content)
            logging.info("PDF Downloaded")
            return filename
        raise NoPDFLinkFound

    def start_scrape(self):
        url = self.get_pdf_url()
        if not url:
            raise NoPDFLinkFound
        res = self.download_pdf(url)
        self.session.close()
        return res


class AJMC(Site):
    """
        Samples:
            https://www.ajmc.com/view/amyotrophic-lateral-sclerosis-disease-state-overview
            https://www.ajmc.com/view/introduction-to-pseudobulbar-affect-setting-the-stage-for-recognition-and-familiarity-with-this-challenging-disorder
    """
    def __init__(self, url, download_dir, pdf_name):
        super().__init__()
        self.url = url
        self.download_path = download_dir
        self.pdf_name = pdf_name
        self.driver = webdriver.Chrome(executable_path=get_driver_path(), options=chrome_options)

        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
        }
        self.session = requests.session()
        self.session.headers.update(self.headers)

    @retry(Exception, tries=5, delay=2)
    def get_page_source(self):
        self.driver.get(self.url)
        return self.driver.page_source

    def get_pdf_url(self, **args):
        try:
            html = self.get_page_source()
            soup = BeautifulSoup(html, "html.parser")
            pdf_href = soup.find("figure", class_="d-block pdf-figure figure").find("a", href=True)['href']
            return pdf_href
        except Exception:
            raise NoPDFLinkFound

    @retry(Exception, tries=5, delay=2)
    def download_pdf(self, url):
        downloadable = is_downloadable(self.session, url)
        if downloadable:
            r = self.session.get(url, allow_redirects=True)
            filename = self.pdf_name
            full_path = os.path.join(self.download_path, filename)
            with open(full_path, 'wb') as writer:
                writer.write(r.content)
            logging.info("PDF Downloaded")
            return filename
        raise NoPDFLinkFound

    def start_scrape(self):
        url = self.get_pdf_url()
        if not url:
            raise NoPDFLinkFound
        res = self.download_pdf(url)
        self.session.close()
        return res


class Nature(Site):
    """
        Samples:
            https://www.nature.com/articles/leu201580
    """
    def __init__(self, url, download_dir, pdf_name):
        super().__init__()
        self.url = url
        self.download_path = download_dir
        self.pdf_name = pdf_name

        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
        }
        self.session = requests.session()
        self.session.headers.update(self.headers)

    @retry(Exception, tries=5, delay=2)
    def get_page_source(self):
        return self.session.get(self.url, headers=self.headers)

    def get_pdf_url(self, **args):
        try:
            html = self.get_page_source().content
            soup = BeautifulSoup(html, "html.parser")
            pdf_href = soup.find("div", class_="c-pdf-download u-clear-both").find("a", class_="c-pdf-download__link",
                                                                                   href=True)['href']
            parsed_url = urlparse(self.url)
            root_url = "{scheme}://{netloc}".format(scheme=parsed_url.scheme,
                                                    netloc=parsed_url.netloc)
            pdf_link = root_url + pdf_href
            return pdf_link
        except Exception:
            raise NoPDFLinkFound

    @retry(Exception, tries=5, delay=2)
    def download_pdf(self, url):
        downloadable = is_downloadable(self.session, url)
        if downloadable:
            r = self.session.get(url, allow_redirects=True)
            filename = self.pdf_name
            full_path = os.path.join(self.download_path, filename)
            with open(full_path, 'wb') as writer:
                writer.write(r.content)
            logging.info("PDF Downloaded")
            return filename
        raise NoPDFLinkFound

    def start_scrape(self):
        url = self.get_pdf_url()
        if not url:
            raise NoPDFLinkFound
        res = self.download_pdf(url)
        self.session.close()
        return res


class BMJ(Site):
    """
        Samples:
            https://ard.bmj.com/content/74/7/1474.long
            https://jnnp.bmj.com/lookup/pmidlookup?view=long&pmid=26203157
    """
    def __init__(self, url, download_dir, pdf_name):
        super().__init__()
        self.url = url
        self.download_path = download_dir
        self.pdf_name = pdf_name

        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
        }
        self.session = requests.session()
        self.session.headers.update(self.headers)

    @retry(Exception, tries=5, delay=2)
    def get_page_source(self):
        return self.session.get(self.url, headers=self.headers)

    def get_pdf_url(self, **args):
        html = self.get_page_source().content
        soup = BeautifulSoup(html, "html.parser")
        pdf_href = soup.find_all("a", class_="article-pdf-download", href=True)
        if len(pdf_href) > 1:
            pdf_href = pdf_href[1]['href']
            if "?with-ds=yes" in str(pdf_href):
                pdf_href = str(pdf_href)
        else:
            pdf_href = str(pdf_href[0]['href'])
        try:
            parsed_url = urlparse(self.url)
            root_url = "{scheme}://{netloc}".format(scheme=parsed_url.scheme,
                                                    netloc=parsed_url.netloc)
            pdf_link = root_url + pdf_href
            return pdf_link
        except Exception:
            raise NoPDFLinkFound

    @retry(Exception, tries=5, delay=2)
    def download_pdf(self, url):
        try:
            r = self.session.get(url, allow_redirects=True)
            filename = self.pdf_name
            full_path = os.path.join(self.download_path, filename)
            with open(full_path, 'wb') as writer:
                writer.write(r.content)
            logging.info("PDF Downloaded")
            return filename
        except Exception:
            raise NoPDFLinkFound

    def start_scrape(self):
        url = self.get_pdf_url()
        if not url:
            raise NoPDFLinkFound
        res = self.download_pdf(url)
        self.session.close()
        return res


class Biologists(Site):
    """
        Samples:
            https://dmm.biologists.org/content/10/5/537.long
            https://jcs.biologists.org/content/132/7/jcs220061.long
    """
    def __init__(self, url, download_dir, pdf_name):
        super().__init__()
        self.url = url
        self.download_path = download_dir
        self.pdf_name = pdf_name

        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
        }
        self.session = requests.session()
        self.session.headers.update(self.headers)

    @retry(Exception, tries=5, delay=2)
    def get_page_source(self):
        return self.session.get(self.url, headers=self.headers)

    def get_pdf_url(self, **args):
        html = self.get_page_source().content
        soup = BeautifulSoup(html, "html.parser")
        pdf_link = soup.find("meta", {"name": "citation_pdf_url"})['content']

        if not is_downloadable(self.session, pdf_link) or pdf_link is None:
            raise NoPDFLinkFound

        pdf_link_with_ds = pdf_link + "?with-ds=yes"
        if is_downloadable(self.session, pdf_link_with_ds):
            pdf_link = pdf_link_with_ds
        return pdf_link

    @retry(Exception, tries=5, delay=2)
    def download_pdf(self, url):
        try:
            r = self.session.get(url, allow_redirects=True)
            filename = self.pdf_name
            full_path = os.path.join(self.download_path, filename)
            with open(full_path, 'wb') as writer:
                writer.write(r.content)
            logging.info("PDF Downloaded")
            return filename
        except Exception:
            raise NoPDFLinkFound

    def start_scrape(self):
        url = self.get_pdf_url()
        if not url:
            raise NoPDFLinkFound
        res = self.download_pdf(url)
        self.session.close()
        return res


class Karger(Site):
    """
        Samples:
            https://www.karger.com/Article/FullText/506259
    """
    def __init__(self, url, download_dir, pdf_name):
        super().__init__()
        self.url = url
        self.download_path = download_dir
        self.pdf_name = pdf_name

        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
        }
        self.session = requests.session()
        self.session.headers.update(self.headers)

    @retry(Exception, tries=5, delay=2)
    def get_page_source(self):
        return self.session.get(self.url, headers=self.headers)

    def get_pdf_url(self, **args):
        html = self.get_page_source().content
        soup = BeautifulSoup(html, "html.parser")
        pdf_href = soup.find("a", {"onclick": "ga('send', 'event', 'FullText', 'Download', 'FullText PDF');"},
                             href=True)['href']

        parsed_url = urlparse(self.url)
        root_url = "{scheme}://{netloc}".format(scheme=parsed_url.scheme,
                                                netloc=parsed_url.netloc)
        pdf_link = root_url + pdf_href

        if is_downloadable(self.session, pdf_link):
            return pdf_link
        raise NoPDFLinkFound

    def download_pdf(self, url):
        try:
            r = self.session.get(url, allow_redirects=True)
            filename = self.pdf_name
            full_path = os.path.join(self.download_path, filename)
            with open(full_path, 'wb') as writer:
                writer.write(r.content)
            logging.info("PDF Downloaded")
            return filename
        except Exception:
            raise NoPDFLinkFound

    def start_scrape(self):
        url = self.get_pdf_url()
        if not url:
            raise NoPDFLinkFound
        res = self.download_pdf(url)
        self.session.close()
        return res


class Wiley(Site):
    """
        Samples:
            https://onlinelibrary.wiley.com/doi/full/10.1111/resp.13525
            https://onlinelibrary.wiley.com/doi/full/10.1002/ajh.24300
            https://onlinelibrary.wiley.com/doi/full/10.1111/jnc.13945
    """
    def __init__(self, url, download_dir, pdf_name):
        super().__init__()
        self.url = url
        self.download_path = download_dir
        self.pdf_name = pdf_name

        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": self.download_path,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing_for_trusted_sources_enabled": False,
            "safebrowsing.enabled": False,
            "plugins.plugins_list": [{"enabled": False, "name": "Chrome PDF Viewer"}],
            "download.extensions_to_open": "applications/pdf"
        })

        self.driver = webdriver.Chrome(executable_path=get_driver_path(), options=chrome_options)
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
        }
        self.session = requests.session()
        self.session.headers.update(self.headers)

        self.pdf_url = ""

    def get_downloaded_file_name(self):
        downloaded_files = os.listdir(self.download_path)
        for f in downloaded_files:
            file_name = Path(f).stem
            # Check if the file name is not an integer
            try:
                int(file_name)
            except Exception:
                return f
        return False


    """
        Source: https://stackoverflow.com/a/51949811
    """
    def download_wait(self, directory, timeout, nfiles=None):
        """
        Wait for downloads to finish with a specified timeout.

        Args
        ----
        directory : str
            The path to the folder where the files will be downloaded.
        timeout : int
            How many seconds to wait until timing out.
        nfiles : int, defaults to None
            If provided, also wait for the expected number of files.

        """
        seconds = 0
        dl_wait = True
        while dl_wait and seconds < timeout:
            time.sleep(1)
            dl_wait = False
            files = os.listdir(directory)
            if nfiles and len(files) != nfiles:
                dl_wait = True

            for fname in files:
                if fname.endswith('.crdownload'):
                    dl_wait = True

            seconds += 1
        return seconds

    """
        Source: https://medium.com/@moungpeter/how-to-automate-downloading-files-using-python-selenium-and-headless-chrome-9014f0cdd196
    """
    def enable_download_headless(self, browser, download_dir):
        browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
        params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
        browser.execute("send_command", params)

    """
        First Step
    """
    @retry(Exception, tries=5, delay=2)
    def get_page_source(self):
        self.driver.get(self.url)
        return self.driver.page_source

    def get_pdf_page_url(self):
        html = self.get_page_source()
        soup = BeautifulSoup(html, "html.parser")
        try:
            pdf_href = soup.find("a", href=True, class_="coolBar__ctrl pdf-download")['href']
            if pdf_href is not None:
                parsed_url = urlparse(self.url)
                root_url = "{scheme}://{netloc}".format(scheme=parsed_url.scheme,
                                                        netloc=parsed_url.netloc)
                full_link = root_url + pdf_href
                self.driver.get(full_link)
                self.pdf_url = pdf_href
                return pdf_href
            raise NoPDFLinkFound
        except Exception:
            raise NoPDFLinkFound

    def get_pdf_url(self, **args):
        pass

    def download_pdf(self, **args):
        self.enable_download_headless(self.driver, self.download_path)

        try:
            download_button = self.driver.find_element_by_css_selector('#app-navbar > div.btn-group.navbar-right > div.grouped.right > a')
            self.driver.get(download_button.get_attribute("href"))
            download_button.click()
        except Exception as e:
            print("Authorization required to download the PDF")
            raise DownloadOperationException
        self.download_wait(self.download_path, 30)
        file_name = self.get_downloaded_file_name()
        old_path = os.path.join(self.download_path, file_name)
        new_path = os.path.join(self.download_path, self.pdf_name)
        time.sleep(2)
        rename_file(old_path, new_path)
        return self.pdf_name

    def start_scrape(self):
        self.get_page_source()
        self.get_pdf_page_url()
        pdf_name = self.download_pdf()
        self.driver.quit()
        self.session.close()
        return pdf_name


class UnknownSite(Site):
    def __init__(self, url, download_dir):
        super().__init__()
        self.url = url
        self.download_path = download_dir

        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
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
