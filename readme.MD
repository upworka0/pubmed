Extracting data form Pubmed website using Python
================================================

The purpose of this project is to extract data of articles from pubmed website using python.
<br>
Python version is Python3.

Installation
------------

Install python package using pip

    pip install -r requirements.txt



How to run:
------------

Run following commands:

    $ python main.py --keyword=<Keyword>

    Example
    $ python main.py --keyword="coronavirus covid-19 pregnancy"
    

How to check results
--------------------

From output folder inside project, You can see the csv and excel files named as keyword variable's value.

----------------------------------------------------------------------------------------------------------------
<br />

Running Web Interface
=====================

Installation
------------

Install python package using pip

    pip3 install -r requirements.txt
    
How to run
----------

Run following commands:

    $ python3 app.py

and check the link http://127.0.0.1:5000/

<br />

Set up on MAC OS
=================

Packages Installation
---------------------

    pip3 install -r requirements.txt


Set the startup application as Login Item in settings.
------------------------------------------------------
  Please refer following link
  <a href="https://stackoverflow.com/questions/6442364/running-script-upon-login-mac">https://stackoverflow.com/questions/6442364/running-script-upon-login-mac </a>

Check web application
---------------------
 After login, you can check http://127.0.0.1:8000/