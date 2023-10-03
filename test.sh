#/bin/bash
FLASK_APP=entrypoints/flask_app.py FLASK_DEBUG=1 PYTHONUNBUFFERED=1 flask run --host=0.0.0.0 --port=5005 &> /dev/null &
flaskpid=$!

python3 entrypoints/redis_event_consumer.py &> /dev/null &
redis_event_consumer_pid=$!

pytest
kill $flaskpid
kill $redis_event_consumer_pid
