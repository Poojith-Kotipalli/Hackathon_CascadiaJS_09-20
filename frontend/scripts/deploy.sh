#!/bin/bash

# RegWatch AI Deployment Script
# Prepares the application for production deployment

set -e

echo "🚀 RegWatch AI Deployment Script"
echo "================================"

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ package.json not found. Please run this script from the project root."
    exit 1
fi

# Check if this is a RegWatch AI project
if ! grep -q "regwatch-ai" package.json; then
    echo "❌ This doesn't appear to be a RegWatch AI project."
    exit 1
fi

echo "✅ RegWatch AI project detected"

# Clean previous builds
echo ""
echo "🧹 Cleaning previous builds..."
rm -rf .next
rm -rf dist
rm -rf build

# Install production dependencies
echo ""
echo "📦 Installing production dependencies..."
npm ci --only=production

# Build the application
echo ""
echo "🔨 Building application..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Build completed successfully"

# Create production environment template
echo ""
echo "⚙️  Creating production environment template..."

cat > .env.production.template << 'EOF'
# RegWatch AI Production Configuration
# Copy this file to .env.production and update values

# API Configuration
NEXT_PUBLIC_API_BASE=https://your-api-domain.com/api/

# Database Configuration (PostgreSQL recommended for production)
DATABASE_URL=postgresql://username:password@host:5432/regwatch_ai

# Security
NODE_ENV=production

# Optional: Analytics and monitoring
# VERCEL_ANALYTICS_ID=your_analytics_id
EOF

echo "✅ Created .env.production.template"

# Create deployment package
echo ""
echo "📦 Creating deployment package..."

# Create deployment directory
mkdir -p deploy
cd deploy

# Copy necessary files
cp -r ../.next .
cp -r ../public .
cp -r ../server .
cp -r ../scripts .
cp ../package.json .
cp ../next.config.mjs .
cp ../.env.production.template .

# Create production package.json
cat > package.json << 'EOF'
{
  "name": "regwatch-ai-production",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "start": "next start",
    "start:api": "node server/index.js",
    "start:full": "concurrently \"npm run start\" \"npm run start:api\"",
    "db:setup": "node scripts/setup-database.js"
  },
  "dependencies": {
    "next": "15.1.3",
    "react": "19.0.0",
    "react-dom": "19.0.0",
    "express": "^4.21.2",
    "cors": "^2.8.5",
    "sqlite3": "^5.1.7",
    "concurrently": "^9.1.0"
  }
}
EOF

# Create production startup script
cat > start-production.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting RegWatch AI Production Servers..."

# Check if environment file exists
if [ ! -f ".env.production" ]; then
    echo "❌ .env.production file not found"
    echo "   Please copy .env.production.template to .env.production and configure it"
    exit 1
fi

# Load environment variables
export $(cat .env.production | grep -v '^#' | xargs)

# Set up database if needed
if [ ! -f "database.sqlite" ] && [[ $DATABASE_URL == *"sqlite"* ]]; then
    echo "📊 Setting up database..."
    npm run db:setup
fi

# Start servers
echo "🌐 Frontend: http://localhost:3000"
echo "🔌 API: http://localhost:3001"
echo ""
npm run start:full
EOF

chmod +x start-production.sh

# Create Docker files
cat > Dockerfile << 'EOF'
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy built application
COPY . .

# Expose ports
EXPOSE 3000 3001

# Start command
CMD ["npm", "run", "start:full"]
EOF

cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  regwatch-ai:
    build: .
    ports:
      - "3000:3000"
      - "3001:3001"
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_BASE=http://localhost:3001/api/
      - DATABASE_URL=./database.sqlite
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  # Optional: PostgreSQL database
  # postgres:
  #   image: postgres:15
  #   environment:
  #     POSTGRES_DB: regwatch_ai
  #     POSTGRES_USER: regwatch
  #     POSTGRES_PASSWORD: your_password
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data
  #   ports:
  #     - "5432:5432"

# volumes:
#   postgres_data:
EOF

cd ..

echo "✅ Deployment package created in ./deploy/"

# Create deployment instructions
cat > DEPLOYMENT.md << 'EOF'
# RegWatch AI Deployment Guide

## Deployment Package

The `./deploy/` directory contains everything needed for production deployment.

## Deployment Options

### 1. Vercel (Recommended for Frontend)

```bash
# Deploy frontend to Vercel
cd deploy
vercel --prod
