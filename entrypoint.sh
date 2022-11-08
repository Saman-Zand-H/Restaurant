#!/bin/bash

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

python manage.py makemigrations && python manage.py migrate
python manage.py collectstatic --noinput
python manage.py search_index --rebuild -f
python manage.py compilemessages
python manage.py update_permissions
python manage.py shell < populate_type_subtype.py
if [ "$DJANGO_ENV" = "production" ]
then
  echo "Starting daphne..."
  daphne -b 0.0.0.0:8000 conf.asgi:application
fi
/etc/init.d/celeryd start

exec "$@"