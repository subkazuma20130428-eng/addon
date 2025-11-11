release: python manage.py migrate
web: gunicorn project.wsgi:application --bind 0.0.0.0:$PORT
