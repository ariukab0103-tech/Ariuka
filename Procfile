web: gunicorn --bind 0.0.0.0:$PORT --timeout 180 --graceful-timeout 30 --worker-class gthread --threads 3 --access-logfile - --error-logfile - run:app
