import re
import csv
import pandas as pd
import time
from functools import wraps
from pandas.io.excel import ExcelWriter

pd.set_option('display.max_rows', 1000)
NIHGOV_BASE = "ncbi.nlm.nih.gov"


def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.
    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry
    :param ExceptionToCheck: the exception to check. may be a tuple of
        exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """
    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry


def csv_parser(csv_path):
    data = pd.read_csv(csv_path)
    return data


def parse_urls(urls):
    urls = urls.replace("\n", "")

    if ',' in urls:
        return urls.split(',')
    return [urls]


def contains_nihgov(urls: list):
    for url in urls:
        if NIHGOV_BASE in url:
            return True
    return False


def get_nihgov_url(urls: list):
    for url in urls:
        if NIHGOV_BASE in url:
            return url


def is_downloadable(session, url):
    """
    Check if the url contains a downloadable resource
    """
    h = session.head(url, allow_redirects=True)
    header = h.headers
    content_type = header.get('content-type')
    if 'text' in content_type.lower():
        return False
    if 'html' in content_type.lower():
        return False
    return True


def get_filename_from_cd(cd):
    """
    Get filename from content-disposition
    """
    if not cd:
        return None
    fname = re.findall('filename=(.+)', cd)
    if len(fname) == 0:
        return None
    return fname[0].strip("\"")
