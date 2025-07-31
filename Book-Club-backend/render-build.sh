#!/usr/bin/env bash
# Render.com Build Script for Book Club Backend
# This script runs after successful deployment

set -o errexit  # Exit on error

echo "🚀 Starting Render.com post-deployment setup..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
echo "🗄️  Running database migrations..."
python manage.py migrate

# Create initial admin user if it doesn't exist
echo "👤 Creating initial admin user..."
python manage.py create_initial_admin

# Check if seeding should run on startup
if [[ "${SEED_ON_STARTUP}" == "true" ]]; then
    echo "🌱 SEED_ON_STARTUP is enabled - running production seeding..."
    python manage.py master_seed --level=production
else
    echo "⏭️  SEED_ON_STARTUP is disabled - skipping automatic seeding"
    echo "💡 To seed manually, run: python manage.py master_seed --level=production"
fi

echo "✅ Render.com post-deployment setup completed successfully!"
