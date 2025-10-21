#!/bin/bash

echo "🔨 Building Bay Club Booking Assistant..."
echo "=========================================="

# Check Python version
python3 --version || { echo "❌ Python 3 not found. Please install Python 3.9+"; exit 1; }

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet

# Install Python dependencies
echo "📚 Installing Python packages..."
pip install -r requirements.txt --quiet

# Install Playwright browsers
echo "🌐 Installing Playwright browser (Chromium)..."
playwright install chromium

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "⚠️  Please edit .env with your credentials:"
        echo "   - BAY_CLUB_USERNAME"
        echo "   - BAY_CLUB_PASSWORD"
        echo "   - DIGITALOCEAN_INFERENCE_KEY (optional)"
    else
        echo "BAY_CLUB_USERNAME=your_email@example.com" > .env
        echo "BAY_CLUB_PASSWORD=your_password" >> .env
        echo "DIGITALOCEAN_INFERENCE_KEY=your_api_key" >> .env
        echo "DEFAULT_HEADLESS=True" >> .env
        echo "⚠️  .env file created. Please edit it with your credentials."
    fi
else
    echo "✅ .env file already exists"
fi

echo ""
echo "=========================================="
echo "✅ Build complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Edit .env with your Bay Club credentials"
echo "  2. Run: ./run-web.sh (for web interface)"
echo "  3. Or run: ./run-cli.sh (for command line)"
echo ""

