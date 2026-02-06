#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Checking if database needs seeding..."
RECORD_COUNT=$(python manage.py shell -c "from core.models import Customer; print(Customer.objects.count())")

if [ "$RECORD_COUNT" -eq "0" ]; then
    echo "Database is empty. Running data simulation..."
    python manage.py simulate_data --years 2 --customers-per-year 500 --products-per-year 50
else
    echo "Database already contains $RECORD_COUNT customers. Skipping simulation."
fi

echo "Starting server..."
exec "$@"
