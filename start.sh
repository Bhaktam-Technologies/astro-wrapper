#!/bin/sh
ALLOW_PUBLIC_ACCESS=1 gunicorn --workers 3 --timeout 12000 -b :5002 wsgi:app --reload
#  lsof -t -i :5002 | xargs kill -9