#/bin/bash
FLASK_APP=entrypoints/flask_app.py FLASK_DEBUG=1 PYTHONUNBUFFERED=1 flask run --host=0.0.0.0 --port=5005 &
flaskpid=$!

pytest
kill $flaskpid
