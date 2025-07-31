#!/bin/bash

echo "🔧 Setting up Local Development Environment for Book Club App"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.local .env
    echo "✅ .env file created. Please edit it with your actual values."
fi

# Activate virtual environment
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
else
    echo "❗ Virtual environment not found. Creating one..."
    python -m venv venv
    source venv/bin/activate
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run migrations
echo "🗄️ Running database migrations..."
export $(cat .env | xargs)
python manage.py migrate

# Create superuser if needed
echo "👤 Do you want to create a superuser? (y/n)"
read -r create_superuser
if [ "$create_superuser" = "y" ]; then
    python manage.py createsuperuser
fi

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

echo "✅ Local development setup complete!"
echo ""
echo "🚀 To start the backend server:"
echo "   ./run_local_backend.sh"
echo ""
echo "🌐 Backend will be available at: http://localhost:8000"
echo "🔧 Admin panel at: http://localhost:8000/admin"
echo "📊 API endpoints at: http://localhost:8000/api/"
