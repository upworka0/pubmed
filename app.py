#!/usr/bin/env python
from flask import Flask, render_template, request, url_for, jsonify
import requests
from scrap_module import ScrapingUnit

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
    keyword = request.form.get('keyword')
    unit = ScrapingUnit(keyword=keyword)
    results = unit.do_scraping()
    return jsonify(results)



if __name__ == '__main__':
    app.run(debug=True)
