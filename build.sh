#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

# Load initial data (only if database is empty)
python manage.py load_initial_data

# Create superadmin from environment variables (only if not exists)
python manage.py create_superadmin
