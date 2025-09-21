# RegWatch AI - Compliance Marketplace

RegWatch AI is a comprehensive marketplace platform with AI-powered regulatory compliance monitoring. It helps sellers ensure their products meet regulatory requirements while providing compliance officers with tools to manage violations and appeals.

## Features

- **Marketplace Interface**: Browse and search product listings with compliance status
- **Seller Dashboard**: Add listings, manage inventory, and track compliance
- **Compliance Console**: Review flags, handle appeals, and manage banned products
- **Mock Mode**: Full offline development with sample data
- **Real-time Compliance**: Automated scanning with detailed violation reports
- **Appeals System**: Sellers can appeal compliance decisions

## Tech Stack

- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS
- **Backend**: Express.js, SQLite
- **UI Components**: Radix UI, shadcn/ui
- **Styling**: Tailwind CSS v4 with dark mode support

## Quick Start

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. **Clone and install dependencies:**
   \`\`\`bash
   git clone <repository-url>
   cd regwatch-ai
   npm install
   \`\`\`

2. **Set up the database:**
   \`\`\`bash
   npm run db:setup
   \`\`\`

3. **Start development servers:**
   \`\`\`bash
   # Start both frontend and API server
   npm run dev:full
   
   # Or start individually:
   npm run dev      # Frontend only (port 3000)
   npm run dev:api  # API server only (port 3001)
   \`\`\`

4. **Access the application:**
   - Frontend: http://localhost:3000
   - API: http://localhost:3001
   - Mock Mode: http://localhost:3000?mock=1

## Development Modes

### Live Mode (Default)
- Connects to the Express.js API server
- Uses SQLite database
- Full CRUD operations
- Real compliance scanning

### Mock Mode (?mock=1)
- Runs entirely in the browser
- Uses in-memory data
- Perfect for offline development
- Sample compliance data included

## Project Structure

\`\`\`
regwatch-ai/
├── app/                    # Next.js app router pages
│   ├── products/          # Marketplace listings
│   ├── sell/              # Add new listings
│   ├── seller/listings/   # Seller dashboard
│   ├── console/           # Compliance console
│   └── debug/             # Debug tools
├── components/            # React components
│   ├── ui/               # shadcn/ui components
│   ├── console/          # Compliance console components
│   └── ...               # Feature components
├── lib/                  # Utilities and types
├── server/               # Express.js API server
├── scripts/              # Database and setup scripts
└── public/               # Static assets
\`\`\`

## API Endpoints

### Products
- `GET /api/products` - List all products
- `GET /api/products?seller_id=me` - Get seller's products
- `POST /api/products` - Create new product
- `PATCH /api/products/:id` - Update product
- `POST /api/products/:id/recheck` - Trigger compliance scan

### Compliance
- `GET /api/flags` - Get compliance flags
- `GET /api/appeals` - Get appeals
- `POST /api/appeals` - Submit appeal
- `POST /api/appeals/:id/resolve` - Resolve appeal

### Moderation
- `POST /api/moderation/ban` - Ban product
- `POST /api/moderation/reinstate` - Reinstate product

## Database Schema

### Products Table
- Basic product information (title, description, price, etc.)
- Status tracking (Active, Flagged, Banned)
- Seller and inventory management

### Compliance Results Table
- Compliance scan results
- Violation details and suggestions
- Agent analysis and confidence scores

### Flags Table
- Compliance violations requiring review
- Severity levels and reasons
- Review status tracking

### Appeals Table
- Seller appeals for banned/flagged items
- Status tracking (pending, approved, rejected)
- Resolution timestamps

## Environment Variables

Create a `.env.local` file:

\`\`\`env
# API Configuration
NEXT_PUBLIC_API_BASE=http://localhost:3001/api/

# Database (SQLite file location)
DATABASE_URL=./database.sqlite

# Optional: Production database
# DATABASE_URL=postgresql://username:password@localhost:5432/regwatch_ai
\`\`\`

## Scripts

- `npm run dev` - Start Next.js development server
- `npm run dev:api` - Start Express.js API server
- `npm run dev:full` - Start both servers concurrently
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run db:setup` - Initialize database with sample data
- `npm run setup` - Full setup (install + database)

## Deployment

### Vercel (Recommended)

1. **Deploy frontend to Vercel:**
   \`\`\`bash
   npm run build
   vercel --prod
   \`\`\`

2. **Deploy API separately or use Vercel Functions:**
   - Option A: Deploy API to a separate service (Railway, Render, etc.)
   - Option B: Convert to Vercel API routes (see deployment guide)

### Self-Hosted

1. **Build the application:**
   \`\`\`bash
   npm run build
   \`\`\`

2. **Set up production database:**
   \`\`\`bash
   # For PostgreSQL
   DATABASE_URL=postgresql://user:pass@host:5432/regwatch_ai npm run db:setup
   \`\`\`

3. **Start production servers:**
   \`\`\`bash
   npm run start        # Frontend
   npm run dev:api      # API (or use PM2/Docker)
   \`\`\`

## Mock Data

The application includes comprehensive mock data for offline development:

- 8 sample products across different categories
- Compliance results with various severity levels
- Sample flags and appeals
- Different seller accounts

Access mock mode by adding `?mock=1` to any URL.

## Compliance System

### Agent Types
- **CPSC_Safety_Agent**: Consumer product safety
- **FDA_Drug_Agent**: Pharmaceutical regulations
- **FDA_Food_Agent**: Food safety and labeling
- **FDA_Device_Agent**: Medical device compliance

### Severity Levels
- **Critical**: Immediate ban required
- **High**: Flagged for review
- **Medium**: Warning with suggestions
- **Low**: Minor compliance notes

### Workflow
1. Product submitted → Automatic compliance scan
2. Non-compliant items → Flagged or banned
3. Sellers can appeal decisions
4. Officers review and resolve appeals

## Development Tips

1. **Use Mock Mode** for rapid development without API dependencies
2. **Debug Console** (`/debug`) provides API testing and system status
3. **Hot Reload** works for both frontend and API changes
4. **TypeScript** provides full type safety across the stack

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test in both live and mock modes
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
1. Check the Debug Console (`/debug`) for system status
2. Review the API logs in the terminal
3. Test in Mock Mode to isolate frontend issues
4. Open an issue on GitHub

---

Built with ❤️ using Next.js, React, and modern web technologies.
