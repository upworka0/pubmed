import requests
import re
import os
from dotenv import load_dotenv
from time import sleep
from bs4 import BeautifulSoup
from multiprocessing import Process, Manager
BASE_URL = "https://www.clinicaltrials.gov/ct2/results"
load_dotenv()

API_KEY = os.environ.get('API_KEY')
PREMIUM_PROXY = os.environ.get('PREMIUM_PROXY')
CREDENTIAL = os.environ.get('CREDENTIAL')


def parse_soup(content):
    return BeautifulSoup(content, 'html.parser')


def get_query_id(content):
    total_count = 0
    soup = parse_soup(content)

    wrappers = soup.select('.ct-inner_content_wrapper > .w3-center')
    if len(wrappers) > 1:
        total_count = int(wrappers[0].text.split(' ')[0])

    script = soup.find('script', text=re.compile('use strict'))
    if script:
        script_text = script.contents[0]
        _group = re.search('ct2/results/rpc/(.*)"', script_text)
        if _group is not None:
            return _group.group(1), total_count
        else:
            print('Not found group on script tag')
        return None, None
    else:
        print('Not found Script Tag')


class MultiThread(Process):
    """
        Threading module
        """
    def __init__(self, _range, query_id, results):
        super(MultiThread, self).__init__()
        self._range = _range
        self.query_id = query_id
        self.results = results

    def run(self):
        clinical = Clinical(query_id=self.query_id, page_range=self._range)
        records = clinical.run()
        self.results.extend(records)


class Clinical:
    """
    Extract data from clilical using requests module
    """

    def __init__(self, query_id=None, page_range=None):
        self.post_url = ''
        self.query_id = query_id
        self.page_range = page_range
        self.header = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
        }
        self.premium_proxy = {
            'http': 'http://{}@{}'.format(CREDENTIAL, PREMIUM_PROXY),
            'https': 'https://{}@{}'.format(CREDENTIAL, PREMIUM_PROXY)
        }

    def get_thread_count(self, keyword):
        params = {
            'cond': keyword['conditions_disease'],
            'term': keyword['other_terms']
        }
        res = self.do_request(BASE_URL, params)
        if res is not None:
            return get_query_id(res.text)

    def run(self):
        records = []
        for page in range(self.page_range[0], self.page_range[1]):
            response = self.post_request(page*100)
            if response is None or len(response['data']) == 0:
                break
            # total = response['recordsFiltered']
            records += response['data']
        return records

    def post_request(self, start):
        payload = {
            'start': start,
            'length': 100
        }
        self.post_url = BASE_URL + '/rpc/' + self.query_id
        try:
            response = requests.post(url=self.post_url, headers=self.header, data=payload)
            return response.json()
        except ConnectionError:
            print('Connection Error')
            sleep(1)
            return self.post_request(start)
        except Exception as e:
            print(e)
            return None

    def do_request(self, url, params):
        try:
            response = requests.request('GET', url=url, headers=self.header, params=params)
            return response
        except ConnectionError:
            print('Connection Error')
            sleep(1)
            return self.do_request(url, params)
        except Exception as e:
            print(e)
            return None


def get_thread_range(thread_count, total_count):
    _range = []
    end_number = total_count//100
    if total_count % 100 != 0:
        end_number += 1
    interval = end_number // thread_count + 1
    for i in range(thread_count):
        if (i+1)*interval > end_number:
            if end_number > i*interval:
                _range.append([i*interval, end_number+1])
            break
        thread_range = [i*interval, (i+1)*interval]
        _range.append(thread_range)
    return _range


def get_numbers(keyword):
    """
    Retrieving total NCT numbers by using clinical module
    """
    clinical = Clinical()

    manager = Manager()
    results = manager.list()

    query_id, total_count = clinical.get_thread_count(keyword=keyword)

    if total_count > 20000:
        total_count = 20000

    if total_count > 0:
        threads = []
        thread_count = 20
        ranges = get_thread_range(thread_count=thread_count, total_count=total_count)
        for _range in ranges:
            thread = MultiThread(
                query_id=query_id,
                _range=_range,
                results=results,
            )
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()
        print("Total Count: ", len(results), ranges)
        return results
    return None
