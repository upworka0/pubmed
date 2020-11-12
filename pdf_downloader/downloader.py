import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from .webdriver_utils import get_driver_path
from concurrent.futures import ThreadPoolExecutor, wait
from .helpers import csv_parser, contains_nihgov, parse_urls, get_nihgov_url
import os
from .sites import NIHGov
import pandas as pd
from datetime import datetime
from .exceptions import CanNotCreateFolder

driver_path = get_driver_path()
chrome_options = Options()
chrome_options.add_argument("--headless")


class Downloader:
    def __init__(self, csv_name):
        self.csv_name = csv_name
        self.ts = datetime.now().strftime('%Y-%m-%d-%H-%M_%S')
        self.download_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "downloads",
                                         self.ts)

    def get_data(self):
        csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "downloads",
                                self.csv_name)
        data = csv_parser(csv_path)
        data = data.assign(PDFDownloaded=pd.Series([False]).bool())
        return data

    # def get_fulltext_urls(self):
    #     data = self.get_data()
    #     return data['Full text link']

    def run(self):
        try:
            os.mkdir(self.download_dir)
        except Exception:
            raise CanNotCreateFolder

        data = self.get_data()

        for idx, row in data.iterrows():
            url_list = row['Full text link']
            if not isinstance(url_list, str) or url_list is None:
                continue

            parsed_list = parse_urls(url_list)
            if contains_nihgov(parsed_list):
                try:
                    nihgov_obj = NIHGov(get_nihgov_url(parsed_list), self.download_dir)
                    res = nihgov_obj.start_scrape()
                    if res:
                        data.loc[idx, 'PDFDownloaded'] = res
                        print(res)
                except Exception as e:
                    print(e)
            else:
                for url in parsed_list:
                    url_class = url_classifier(url)
                    if url_class:
                        try:
                            klass = url_class(url, self.download_dir)
                            res = klass.start_scrape()
                            if res:
                                data.loc[idx, 'PDFDownloaded'] = res
                                print(res)
                        except Exception as e:
                            print(e)

        print(data)

        csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports",
                                self.ts + ".csv")
        data.to_csv(csv_path, index=False, header=True)


def url_classifier(url):
    if "eprints.whiterose.ac.uk" in url:
        from .sites import WhiteRose
        return WhiteRose
    return False
