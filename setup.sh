#!/bin/bash

# AI Website Builder Setup Script
# This script will help you set up the AI Website Builder on your system

echo "🚀 AI Website Builder Setup"
echo "============================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18.0 or higher."
    echo "   Download from: https://nodejs.org/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node --version)
echo "✅ Node.js version: $NODE_VERSION"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm."
    exit 1
fi

NPM_VERSION=$(npm --version)
echo "✅ npm version: $NPM_VERSION"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully!"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""

# Create .env.local file
if [ ! -f .env.local ]; then
    echo "⚙️ Creating environment configuration..."
    cp .env.example .env.local
    echo "✅ Created .env.local file"
    echo ""
    echo "🔧 Please edit .env.local and add your OpenAI API key:"
    echo "   OPENAI_API_KEY=your_openai_api_key_here"
    echo ""
else
    echo "✅ .env.local file already exists"
fi

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p public/images
mkdir -p public/templates
mkdir -p data/websites
mkdir -p data/templates
echo "✅ Project directories created"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env.local and add your OpenAI API key"
echo "2. Run 'npm run dev' to start the development server"
echo "3. Open http://localhost:3000 in your browser"
echo ""
echo "For more information, check the README.md file"
echo ""
echo "Happy building! 🚀"