import time
from functools import wraps
import csv
from pandas.io.excel import ExcelWriter
import pandas


def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
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


def write_csv(csv_file, data):
    """
    Write lines to csv named as filename
    """
    with open(csv_file, 'w', encoding='utf-8', newline='') as writeFile:
        writer = csv.writer(writeFile, delimiter=',')
        writer.writerows(data)


def excel_out(csv_file, excel_file):
    # convert csv file to excel format
    with ExcelWriter(excel_file) as ew:
        df = pandas.read_csv(csv_file)
        df.to_excel(ew, sheet_name="sheet1", index=False)


def get_thread_range(thread_count, total_count):
    """
    Divide total units into array of threads
    @return: array
    """
    ranges = []
    for i in range(thread_count):
        ranges.append([])
    count = 0
    while count < total_count:
        for i in range(thread_count):
            count += 1
            ranges[i].append(count-1)
            if count == total_count:
                break

    return ranges
