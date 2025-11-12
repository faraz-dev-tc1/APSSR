#!/bin/bash
# Setup script for Automated Rulebook Consolidation System

set -e

echo "=========================================="
echo "APSSR - Setup Script"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo "✓ Python 3 found: $PYTHON_VERSION"
else
    echo "✗ Python 3 not found. Please install Python 3.9 or higher."
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠ Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ pip upgraded"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Create .env file
echo ""
if [ -f ".env" ]; then
    echo "⚠ .env file already exists. Skipping..."
else
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠ IMPORTANT: Edit .env and add your GOOGLE_API_KEY"
    echo "   Get your key at: https://aistudio.google.com/app/apikey"
fi

# Create directories
echo ""
echo "Creating directories..."
mkdir -p data/input data/output data/reference logs
echo "✓ Directories created"

# Download spaCy model (optional)
echo ""
echo "Do you want to download spaCy language model? (y/N)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "Downloading spaCy model..."
    python -m spacy download en_core_web_sm
    echo "✓ spaCy model downloaded"
else
    echo "⊘ Skipping spaCy model download"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your GOOGLE_API_KEY"
echo "  2. Place PDF files in data/input/"
echo "  3. Run: python main.py data/input/your_file.pdf"
echo ""
echo "For help, see:"
echo "  - QUICKSTART.md for quick guide"
echo "  - README.md for full documentation"
echo "  - ARCHITECTURE.md for technical details"
echo ""
