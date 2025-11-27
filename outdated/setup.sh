#!/bin/bash

# VR Recommendation System Setup Script

echo "🚀 Setting up VR Recommendation System..."

# Check if MongoDB is installed
if ! command -v mongod &> /dev/null; then
    echo "⚠ MongoDB not found. Installing MongoDB..."
    
    # For macOS with Homebrew
    if command -v brew &> /dev/null; then
        brew tap mongodb/brew
        brew install mongodb-community
        echo "✓ MongoDB installed via Homebrew"
    else
        echo "❌ Please install MongoDB manually:"
        echo "   - macOS: brew install mongodb-community"
        echo "   - Ubuntu: sudo apt-get install mongodb"
        echo "   - Windows: Download from https://www.mongodb.com/try/download/community"
        exit 1
    fi
else
    echo "✓ MongoDB found"
fi

# Start MongoDB service
echo "🔄 Starting MongoDB service..."
if command -v brew &> /dev/null; then
    brew services start mongodb/brew/mongodb-community
else
    sudo systemctl start mongod
fi

# Wait for MongoDB to start
sleep 3

# Check if MongoDB is running
if pgrep -x "mongod" > /dev/null; then
    echo "✓ MongoDB is running"
else
    echo "⚠ MongoDB might not be running. Please start it manually."
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To run the VR recommendation system:"
echo "  python vr_recommender.py"
echo ""
echo "To run analytics:"
echo "  python analytics.py"
echo ""
echo "To stop MongoDB:"
echo "  brew services stop mongodb/brew/mongodb-community  # macOS"
echo "  sudo systemctl stop mongod                        # Linux"

