#!bin/bash
/Library/Frameworks/Python.framework/Versions/3.6/bin/gunicorn wsgi:app --workers=4 --threads=2 --daemon