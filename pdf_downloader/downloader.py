import requests
from .helpers import csv_parser, contains_nihgov, parse_urls, get_nihgov_url, get_unique_id_from_url
import os
from .sites import NIHGov
import pandas as pd
from datetime import datetime
from .exceptions import CanNotCreateFolder
from utils import retry


class Downloader:
    def __init__(self, csv_name):
        self.csv_name = csv_name
        self.ts = datetime.now().strftime('%Y-%m-%d-%H-%M_%S')
        self.download_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "downloads",
                                         self.ts)
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
        }
        self.url_resolver_session = requests.session()
        self.url_resolver_session.headers.update(self.headers)

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
            pubmed_link = row['Pubmed link']
            unique_pdf_id = get_unique_id_from_url(pubmed_link) + ".pdf"
            if not isinstance(url_list, str) or url_list is None:
                continue

            parsed_list = parse_urls(url_list)
            if contains_nihgov(parsed_list):
                try:
                    nihgov_obj = NIHGov(get_nihgov_url(parsed_list), self.download_dir, unique_pdf_id)
                    res = nihgov_obj.start_scrape()
                    if res:
                        data.loc[idx, 'PDFDownloaded'] = res
                        print(res, "Source: NIHGov")
                except Exception as e:
                    print(e)
            else:
                for url in parsed_list:
                    if not isinstance(url, str):
                        continue
                    if "http" not in url:
                        continue
                    resolved_url = url_resolver(url, self.url_resolver_session)
                    if resolved_url:
                        if "doi" in resolved_url:
                            resolved_url = url_resolver(resolved_url, self.url_resolver_session)
                    url_class = url_classifier(resolved_url)
                    if resolved_url != url:
                        print("Resolved url: %s -> %s" % (url, resolved_url))
                    if url_class:
                        try:
                            klass = url_class(resolved_url, self.download_dir, unique_pdf_id)
                            res = klass.start_scrape()
                            if res:
                                data.loc[idx, 'PDFDownloaded'] = res
                                print(res, "Source: %s" % type(klass).__name__)
                        except Exception as e:
                            print(e)

        print(data)

        csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports",
                                self.ts + ".csv")
        data.to_csv(csv_path, index=False, header=True)


def url_classifier(url):
    if not url:
        return False
    if "eprints.whiterose.ac.uk" in url:
        from .sites import WhiteRose
        return WhiteRose
    if "iris.unito.it" in url:
        from .sites import UnitoIt
        return UnitoIt
    if "academic.oup" in url:
        from .sites import OUP
        return OUP
    if "ajmc.com" in url:
        from .sites import AJMC
        return AJMC
    if "nature.com" in url:
        from .sites import Nature
        return Nature
    if "bmj.com" in url:
        from .sites import BMJ
        return BMJ
    if "biologists.org" in url:
        from .sites import Biologists
        return Biologists
    if "karger.com" in url:
        from .sites import Karger
        return Karger
    if "wiley.com" in url:
        from .sites import Wiley
        return Wiley
    return False


@retry(Exception, tries=10, delay=0.5, backoff=1)
def url_resolver(url, session):
    if "hdl.handle.net" in url or "doi.org" in url or "doi.wiley.com" in url:
        location = session.head(url).headers.get('Location')
        if location:
            return location
        return False
    if "academic.oup.com" in url and "article-lookup" in url:
        location = session.head(url).headers.get('Location')
        if location:
            if "http" not in location:
                return "https://academic.oup.com" + location
            return location
        return False

    # if "doi" in url:
    #     return session.head(url).headers.get('Location')
    # try:
    #     location = session.head(url).headers.get('Location')
    #     if location:
    #         return location
    #     raise Exception
    # except Exception:
    return url
