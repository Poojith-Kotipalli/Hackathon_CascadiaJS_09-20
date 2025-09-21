#!/bin/bash

# RegWatch AI Installation Script
# This script sets up the complete RegWatch AI application

set -e

echo "🚀 RegWatch AI Installation Script"
echo "=================================="

# Check Node.js version
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18+ is required. Current version: $(node -v)"
    echo "   Please upgrade Node.js: https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js $(node -v) detected"

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not available. Please install npm."
    exit 1
fi

echo "✅ npm $(npm -v) detected"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# Set up environment file
echo ""
echo "⚙️  Setting up environment configuration..."

if [ ! -f ".env.local" ]; then
    cat > .env.local << EOF
# RegWatch AI Configuration
NEXT_PUBLIC_API_BASE=http://localhost:3001/api/

# Database Configuration
DATABASE_URL=./database.sqlite

# Development Settings
NODE_ENV=development
EOF
    echo "✅ Created .env.local with default configuration"
else
    echo "ℹ️  .env.local already exists, skipping..."
fi

# Set up database
echo ""
echo "🗄️  Setting up database..."
npm run db:setup

if [ $? -ne 0 ]; then
    echo "❌ Failed to set up database"
    exit 1
fi

echo "✅ Database initialized with sample data"

# Create startup script
echo ""
echo "📝 Creating startup scripts..."

cat > start-dev.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting RegWatch AI Development Servers..."
echo "Frontend: http://localhost:3000"
echo "API: http://localhost:3001"
echo "Mock Mode: http://localhost:3000?mock=1"
echo ""
echo "Press Ctrl+C to stop all servers"
npm run dev:full
EOF

chmod +x start-dev.sh

cat > start-mock.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting RegWatch AI in Mock Mode..."
echo "Opening: http://localhost:3000?mock=1"
echo ""
npm run dev &
sleep 3
if command -v open &> /dev/null; then
    open "http://localhost:3000?mock=1"
elif command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:3000?mock=1"
fi
wait
EOF

chmod +x start-mock.sh

echo "✅ Created startup scripts:"
echo "   - start-dev.sh (full development mode)"
echo "   - start-mock.sh (mock mode only)"

# Installation complete
echo ""
echo "🎉 Installation Complete!"
echo "========================"
echo ""
echo "Quick Start Options:"
echo ""
echo "1. Full Development Mode (with API):"
echo "   ./start-dev.sh"
echo "   or: npm run dev:full"
echo ""
echo "2. Mock Mode (offline development):"
echo "   ./start-mock.sh"
echo "   or: npm run dev (then visit http://localhost:3000?mock=1)"
echo ""
echo "3. Individual servers:"
echo "   npm run dev      # Frontend only (port 3000)"
echo "   npm run dev:api  # API server only (port 3001)"
echo ""
echo "📚 Documentation:"
echo "   - README.md for detailed setup"
echo "   - /debug page for system status"
echo "   - Mock mode for offline development"
echo ""
echo "🔧 Troubleshooting:"
echo "   - Check /debug page for API status"
echo "   - Use mock mode (?mock=1) for offline work"
echo "   - Run 'npm run db:setup' to reset database"
echo ""
echo "Happy coding! 🚀"
