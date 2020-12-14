#!/usr/bin/env python
import argparse
from scrap_module import Scraping_Job
import os


if __name__ == '__main__':
    # create output folder
    output_folder = "output"
    if not os.path.exists('output'):
        os.mkdir("output")

    # arg parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--keyword', type=str, required=True)
    args = parser.parse_args()

    data, excel_file = Scraping_Job(keyword=args.keyword, result_folder="output")

    print("Scraping was successfully finished.")
    print("Total count of results is %s" % len(data))
    print("Result file is located in %s" % excel_file)
