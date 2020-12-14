#!/usr/bin/env python
from flask import Flask, render_template, request, jsonify, session
import requests
from scrap_module import Scraping_Job
from scrap_pubmed import Pubmed_Job
from clinical import get_numbers
from datetime import datetime
from pdf_downloader.downloader import Downloader

app = Flask(__name__)
app.secret_key = "mSu*B!m+RyQoG_pL3cE-ps~j%.?u-tbt;e-JvHsX$-l]6;Q}"


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("index.html", name="test")


@app.route('/clinical', methods=['GET', 'POST'])
def clinical():
    return render_template("clinical.html")


@app.route('/suggestions')
def get_suggestions():
    term = request.args.get('term')
    url = "https://pubmed.ncbi.nlm.nih.gov/suggestions/?term=%s" % term
    res = requests.get(url)
    return res.text


@app.route('/clinical_scrap', methods=['POST'])
def clinical_scrap():
    print(datetime.now())
    conditions_disease = request.form.get('conditions_disease')
    other_terms = request.form.get('other_terms')
    keyword = {
        'conditions_disease': conditions_disease,
        'other_terms': other_terms
    }
    nct_numbers = get_numbers(keyword=keyword)
    if nct_numbers is None:
        return jsonify({'results': [], 'excel_file': ''})
    results, excel_file, file_name = Pubmed_Job(keyword=keyword, numbers=nct_numbers, result_folder="static/downloads")
    session['csv_name'] = file_name
    print(datetime.now())
    return jsonify({'results': results, 'excel_file': excel_file})


@app.route('/scrap', methods=['POST'])
def scrap():
    print(datetime.now())
    keyword = request.form.get('keyword')
    results, excel_file, file_name = Scraping_Job(keyword=keyword, result_folder="static/downloads")
    session['csv_name'] = file_name
    print(datetime.now())
    return jsonify({'results': results, 'excel_file': excel_file})


@app.route('/download_pdf', methods=['GET'])
def download_pdf():
    if 'csv_name' in session:
        csv_name = session['csv_name'] + ".csv"
        downloader_obj = Downloader(csv_name)
        downloader_obj.run()
        session.pop('csv_name', None)
        return jsonify({'results': "Check downloads folder."})
    return jsonify({'results': "No csv found"})


if __name__ == '__main__':
    app.run(debug=True)
