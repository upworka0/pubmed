import requests
import re
import json
from time import sleep
from bs4 import BeautifulSoup

BASE_URL = "https://www.clinicaltrials.gov/ct2/results"
API_KEY = "H5z4wFvrJCanTSRodUfYDGW9XhxtKm2L"
PROXY = '199.189.86.111:9500'
CREDENTIAL = 'cb78253c9ab1ad416dfe9027b7892823:676f1852dcf3b3c34be7269bafddcd49'


def parse_soup(content):
    return BeautifulSoup(content, 'html.parser')


def get_query_id(content):
    soup = parse_soup(content)
    script = soup.find('script', text=re.compile('use strict'))
    if script:
        script_text = script.contents[0]
        _group = re.search('ct2/results/rpc/(.*)"', script_text)
        if _group is not None:
            return _group.group(1)
        else:
            print('Not found group on script tag')
        return None
    else:
        print('Not found Script Tag')


class Clinical:

    def __init__(self):
        self.post_url = ''
        self.header = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
        }
        self.proxy_endpoint = {
            'http': 'http://{}@{}'.format(CREDENTIAL, PROXY),
            'https': 'https://{}@{}'.format(CREDENTIAL, PROXY),
        }

    def run(self, keyword):
        params = {
            'cond': keyword
        }
        res = self.do_request(BASE_URL, params)
        if res is not None:
            query_id = get_query_id(res.text)
            if query_id is not None:
                self.post_url = BASE_URL + '/rpc/' + query_id
                results = self.rpc_request()
                return results
        else:
            return None

    def rpc_request(self):
        start = 0
        records = []
        while True:
            response = self.post_request(start)
            if response is None:
                continue
            if len(response['data']) == 0:
                break
            total = response['recordsFiltered']
            start += 100
            records.extend(response['data'])
            print(len(records), total)
        return records

    def post_request(self, start):
        payload = {
            'start': start,
            'length': 100
        }
        try:
            response = requests.post(url=self.post_url, headers=self.header, data=payload, proxies=self.proxy_endpoint)
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
            response = requests.request('GET', url=url, headers=self.header, params=params, proxies=self.proxy_endpoint)
            return response
        except ConnectionError:
            print('Connection Error')
            sleep(1)
            return self.do_request(url, params)
        except Exception as e:
            print(e)
            return None


def get_numbers(keyword):
    clinical = Clinical()
    return clinical.run(keyword=keyword)
