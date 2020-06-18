#!bin/sh
/usr/local/bin/gunicorn --chdir /Users/johan/Desktop/pubmed wsgi:app --daemon