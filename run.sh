#!bin/sh
/usr/local/bin/gunicorn --chdir /Users/johan/Desktop/pubmed wsgi:app --workers=4 --threads=2 --daemon