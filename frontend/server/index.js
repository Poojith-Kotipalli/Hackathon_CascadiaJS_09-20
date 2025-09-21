const express = require("express")
const cors = require("cors")
const sqlite3 = require("sqlite3").verbose()
const path = require("path")

const app = express()
const PORT = process.env.PORT || 3001

// Middleware
app.use(cors())
app.use(express.json())

// Database setup
const dbPath = path.join(__dirname, "../database.sqlite")
const db = new sqlite3.Database(dbPath)

// Initialize database tables
db.serialize(() => {
  // Products table
  db.run(`
    CREATE TABLE IF NOT EXISTS products (
      id TEXT PRIMARY KEY,
      seller_id TEXT NOT NULL,
      title TEXT NOT NULL,
      description TEXT NOT NULL,
      category TEXT,
      price REAL,
      inventory INTEGER,
      image_url TEXT,
      status TEXT DEFAULT 'Active',
      last_checked_at TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
  `)

  // Compliance results table
  db.run(`
    CREATE TABLE IF NOT EXISTS compliance_results (
      id TEXT PRIMARY KEY,
      product_id TEXT NOT NULL,
      compliant BOOLEAN NOT NULL,
      violations TEXT,
      suggestions TEXT,
      severity TEXT,
      confidence REAL,
      uses_context BOOLEAN,
      top_rules TEXT,
      agent_summaries TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (product_id) REFERENCES products (id)
    )
  `)

  // Flags table
  db.run(`
    CREATE TABLE IF NOT EXISTS flags (
      id TEXT PRIMARY KEY,
      listing_id TEXT NOT NULL,
      seller_id TEXT NOT NULL,
      severity TEXT NOT NULL,
      reason TEXT NOT NULL,
      reviewed BOOLEAN DEFAULT FALSE,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (listing_id) REFERENCES products (id)
    )
  `)

  // Appeals table
  db.run(`
    CREATE TABLE IF NOT EXISTS appeals (
      id TEXT PRIMARY KEY,
      listing_id TEXT NOT NULL,
      seller_id TEXT NOT NULL,
      reason TEXT NOT NULL,
      status TEXT DEFAULT 'pending',
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      resolved_at TEXT,
      FOREIGN KEY (listing_id) REFERENCES products (id)
    )
  `)
})

// Utility functions
function generateId() {
  return Math.random().toString(36).substr(2, 9)
}

function getCurrentTimestamp() {
  return new Date().toISOString()
}

// Mock compliance data
const mockComplianceResponses = {
  low: {
    compliant: true,
    violations: [],
    suggestions: ["Consider adding more detailed product specifications"],
    severity: "low",
    confidence: 0.85,
    uses_context: true,
    top_rules: ["General product safety guidelines"],
    agent_summaries: [
      {
        agent: "CPSC_Safety_Agent",
        table: "safety_rules",
        score: 0.9,
        compliant: true,
        severity: "low",
        uses_context: true,
        top_rules: ["Basic safety compliance", "Product labeling requirements"],
      },
    ],
  },
  medium: {
    compliant: false,
    violations: ["Missing safety warnings", "Incomplete ingredient list"],
    suggestions: ["Add proper safety warnings", "Include complete ingredient information"],
    severity: "medium",
    confidence: 0.75,
    uses_context: true,
    top_rules: ["FDA labeling requirements", "Consumer safety standards"],
    agent_summaries: [
      {
        agent: "FDA_Food_Agent",
        table: "food_safety_rules",
        score: 0.6,
        compliant: false,
        severity: "medium",
        uses_context: true,
        top_rules: ["Ingredient disclosure", "Allergen warnings"],
      },
    ],
  },
  high: {
    compliant: false,
    violations: ["Prohibited substance detected", "Missing FDA approval", "Safety hazard identified"],
    suggestions: ["Remove prohibited substances", "Obtain FDA approval", "Address safety concerns"],
    severity: "critical",
    confidence: 0.95,
    uses_context: true,
    top_rules: ["FDA drug regulations", "CPSC safety standards", "Prohibited substances list"],
    agent_summaries: [
      {
        agent: "FDA_Drug_Agent",
        table: "drug_regulations",
        score: 0.2,
        compliant: false,
        severity: "critical",
        uses_context: true,
        top_rules: ["Prescription drug regulations", "Controlled substances"],
      },
    ],
  },
}

// API Routes

// Products
app.get("/api/products", (req, res) => {
  const { seller_id } = req.query
  let query = `
    SELECT p.*, cr.compliant, cr.violations, cr.suggestions, cr.severity, 
           cr.confidence, cr.uses_context, cr.top_rules, cr.agent_summaries
    FROM products p
    LEFT JOIN compliance_results cr ON p.id = cr.product_id
  `

  const params = []
  if (seller_id) {
    query += " WHERE p.seller_id = ?"
    params.push(seller_id)
  }

  query += " ORDER BY p.created_at DESC"

  db.all(query, params, (err, rows) => {
    if (err) {
      return res.status(500).json({ error: err.message })
    }

    const products = rows.map((row) => ({
      id: row.id,
      seller_id: row.seller_id,
      title: row.title,
      description: row.description,
      category: row.category,
      price: row.price,
      inventory: row.inventory,
      image_url: row.image_url,
      status: row.status,
      last_checked_at: row.last_checked_at,
      created_at: row.created_at,
      updated_at: row.updated_at,
      compliance:
        row.compliant !== null
          ? {
              compliant: row.compliant,
              violations: JSON.parse(row.violations || "[]"),
              suggestions: JSON.parse(row.suggestions || "[]"),
              severity: row.severity,
              confidence: row.confidence,
              uses_context: row.uses_context,
              top_rules: JSON.parse(row.top_rules || "[]"),
              agent_summaries: JSON.parse(row.agent_summaries || "[]"),
            }
          : null,
    }))

    res.json(products)
  })
})

app.get("/api/products/:id", (req, res) => {
  const { id } = req.params

  const query = `
    SELECT p.*, cr.compliant, cr.violations, cr.suggestions, cr.severity, 
           cr.confidence, cr.uses_context, cr.top_rules, cr.agent_summaries
    FROM products p
    LEFT JOIN compliance_results cr ON p.id = cr.product_id
    WHERE p.id = ?
  `

  db.get(query, [id], (err, row) => {
    if (err) {
      return res.status(500).json({ error: err.message })
    }
    if (!row) {
      return res.status(404).json({ error: "Product not found" })
    }

    const product = {
      id: row.id,
      seller_id: row.seller_id,
      title: row.title,
      description: row.description,
      category: row.category,
      price: row.price,
      inventory: row.inventory,
      image_url: row.image_url,
      status: row.status,
      last_checked_at: row.last_checked_at,
      created_at: row.created_at,
      updated_at: row.updated_at,
      compliance:
        row.compliant !== null
          ? {
              compliant: row.compliant,
              violations: JSON.parse(row.violations || "[]"),
              suggestions: JSON.parse(row.suggestions || "[]"),
              severity: row.severity,
              confidence: row.confidence,
              uses_context: row.uses_context,
              top_rules: JSON.parse(row.top_rules || "[]"),
              agent_summaries: JSON.parse(row.agent_summaries || "[]"),
            }
          : null,
    }

    res.json(product)
  })
})

app.post("/api/products", (req, res) => {
  const { seller_id, title, description, category, price, inventory, image_url } = req.body
  const id = generateId()
  const now = getCurrentTimestamp()

  const query = `
    INSERT INTO products (id, seller_id, title, description, category, price, inventory, image_url, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `

  db.run(query, [id, seller_id, title, description, category, price, inventory, image_url, now, now], (err) => {
    if (err) {
      return res.status(500).json({ error: err.message })
    }

    res.status(201).json({
      id,
      seller_id,
      title,
      description,
      category,
      price,
      inventory,
      image_url,
      status: "Active",
      created_at: now,
      updated_at: now,
    })
  })
})

app.patch("/api/products/:id", (req, res) => {
  const { id } = req.params
  const updates = req.body
  const now = getCurrentTimestamp()

  const fields = Object.keys(updates)
    .map((key) => `${key} = ?`)
    .join(", ")
  const values = [...Object.values(updates), now, id]

  const query = `UPDATE products SET ${fields}, updated_at = ? WHERE id = ?`

  db.run(query, values, function (err) {
    if (err) {
      return res.status(500).json({ error: err.message })
    }
    if (this.changes === 0) {
      return res.status(404).json({ error: "Product not found" })
    }

    res.json({ message: "Product updated successfully" })
  })
})

app.post("/api/products/:id/recheck", (req, res) => {
  const { id } = req.params

  // Simulate compliance check with random result
  const severities = ["low", "medium", "high"]
  const randomSeverity = severities[Math.floor(Math.random() * severities.length)]
  const complianceResult = mockComplianceResponses[randomSeverity]

  // Update product status based on compliance
  let newStatus = "Active"
  if (complianceResult.severity === "critical" || complianceResult.severity === "high") {
    newStatus = "Flagged"
  }

  const now = getCurrentTimestamp()
  const complianceId = generateId()

  // Insert compliance result
  const complianceQuery = `
    INSERT INTO compliance_results (id, product_id, compliant, violations, suggestions, severity, confidence, uses_context, top_rules, agent_summaries, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `

  db.run(
    complianceQuery,
    [
      complianceId,
      id,
      complianceResult.compliant,
      JSON.stringify(complianceResult.violations),
      JSON.stringify(complianceResult.suggestions),
      complianceResult.severity,
      complianceResult.confidence,
      complianceResult.uses_context,
      JSON.stringify(complianceResult.top_rules),
      JSON.stringify(complianceResult.agent_summaries),
      now,
    ],
    (err) => {
      if (err) {
        return res.status(500).json({ error: err.message })
      }

      // Update product status and last_checked_at
      const updateQuery = "UPDATE products SET status = ?, last_checked_at = ? WHERE id = ?"
      db.run(updateQuery, [newStatus, now, id], (err) => {
        if (err) {
          return res.status(500).json({ error: err.message })
        }

        // Create flag if non-compliant
        if (
          !complianceResult.compliant &&
          (complianceResult.severity === "high" || complianceResult.severity === "critical")
        ) {
          const flagId = generateId()
          const flagQuery = `
          INSERT INTO flags (id, listing_id, seller_id, severity, reason, created_at)
          SELECT ?, ?, seller_id, ?, ?, ?
          FROM products WHERE id = ?
        `

          db.run(flagQuery, [flagId, id, complianceResult.severity, complianceResult.violations.join(", "), now, id])
        }

        res.json({ message: "Compliance check completed", result: complianceResult })
      })
    },
  )
})

// Flags
app.get("/api/flags", (req, res) => {
  const query = `
    SELECT f.*, p.title as listing_title, p.image_url as listing_image
    FROM flags f
    JOIN products p ON f.listing_id = p.id
    WHERE f.reviewed = FALSE
    ORDER BY f.created_at DESC
  `

  db.all(query, [], (err, rows) => {
    if (err) {
      return res.status(500).json({ error: err.message })
    }
    res.json(rows)
  })
})

// Appeals
app.get("/api/appeals", (req, res) => {
  const query = `
    SELECT a.*, p.title as listing_title, p.image_url as listing_image
    FROM appeals a
    JOIN products p ON a.listing_id = p.id
    ORDER BY a.created_at DESC
  `

  db.all(query, [], (err, rows) => {
    if (err) {
      return res.status(500).json({ error: err.message })
    }
    res.json(rows)
  })
})

app.post("/api/appeals", (req, res) => {
  const { listing_id, seller_id, reason } = req.body
  const id = generateId()
  const now = getCurrentTimestamp()

  const query = `
    INSERT INTO appeals (id, listing_id, seller_id, reason, created_at)
    VALUES (?, ?, ?, ?, ?)
  `

  db.run(query, [id, listing_id, seller_id, reason, now], (err) => {
    if (err) {
      return res.status(500).json({ error: err.message })
    }

    res.status(201).json({
      id,
      listing_id,
      seller_id,
      reason,
      status: "pending",
      created_at: now,
    })
  })
})

app.post("/api/appeals/:id/resolve", (req, res) => {
  const { id } = req.params
  const { approve } = req.body
  const now = getCurrentTimestamp()
  const status = approve ? "approved" : "rejected"

  const query = "UPDATE appeals SET status = ?, resolved_at = ? WHERE id = ?"

  db.run(query, [status, now, id], function (err) {
    if (err) {
      return res.status(500).json({ error: err.message })
    }
    if (this.changes === 0) {
      return res.status(404).json({ error: "Appeal not found" })
    }

    // If approved, reinstate the product
    if (approve) {
      const reinstateQuery = `
        UPDATE products SET status = 'Active' 
        WHERE id = (SELECT listing_id FROM appeals WHERE id = ?)
      `
      db.run(reinstateQuery, [id])
    }

    res.json({ message: "Appeal resolved successfully" })
  })
})

// Moderation
app.post("/api/moderation/ban", (req, res) => {
  const { product_id, reason } = req.body
  const now = getCurrentTimestamp()

  const query = "UPDATE products SET status = ?, updated_at = ? WHERE id = ?"

  db.run(query, ["Banned", now, product_id], function (err) {
    if (err) {
      return res.status(500).json({ error: err.message })
    }
    if (this.changes === 0) {
      return res.status(404).json({ error: "Product not found" })
    }

    // Mark related flags as reviewed
    const flagQuery = "UPDATE flags SET reviewed = TRUE WHERE listing_id = ?"
    db.run(flagQuery, [product_id])

    res.json({ message: "Product banned successfully" })
  })
})

app.post("/api/moderation/reinstate", (req, res) => {
  const { product_id } = req.body
  const now = getCurrentTimestamp()

  const query = "UPDATE products SET status = ?, updated_at = ? WHERE id = ?"

  db.run(query, ["Active", now, product_id], function (err) {
    if (err) {
      return res.status(500).json({ error: err.message })
    }
    if (this.changes === 0) {
      return res.status(404).json({ error: "Product not found" })
    }

    res.json({ message: "Product reinstated successfully" })
  })
})

// Health check
app.get("/api/health", (req, res) => {
  res.json({ status: "OK", timestamp: getCurrentTimestamp() })
})

app.listen(PORT, () => {
  console.log(`RegWatch AI API server running on port ${PORT}`)
})
