#!/usr/bin/env python
from flask import Flask, render_template, request, url_for


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("index.html", name="test")


if __name__=='__main__':
    app.run(host='0.0.0.0', debug=True)
