#!/usr/bin/env python
from flask import Flask, render_template, request, jsonify
import requests
from scrap_module import Scraping_Job
from datetime import datetime

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("index.html", name="test")


@app.route('/suggestions')
def get_suggestions():
    term = request.args.get('term')
    url = "https://pubmed.ncbi.nlm.nih.gov/suggestions/?term=%s" % term
    res = requests.get(url)
    return res.text


@app.route('/scrap', methods=['POST'])
def scrap():
    print(datetime.now())
    keyword = request.form.get('keyword')
    results, excel_file = Scraping_Job(keyword=keyword, result_folder="static/downloads")
    print(datetime.now())
    return jsonify({'results': results, 'excel_file': excel_file})


if __name__ == '__main__':
    app.run(debug=True)
