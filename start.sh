#!/bin/sh
ALLOW_PUBLIC_ACCESS=1 gunicorn \
  --workers 3 \
  --max-requests 200 \
  --max-requests-jitter 50 \
  --timeout 120 \
  -b :5002 wsgi:app
#  lsof -t -i :5002 | xargs kill -9