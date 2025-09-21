const sqlite3 = require("sqlite3").verbose()
const path = require("path")

const dbPath = path.join(__dirname, "../database.sqlite")
const db = new sqlite3.Database(dbPath)

// Sample data
const sampleProducts = [
  {
    id: "prod_001",
    seller_id: "me",
    title: "Organic Baby Food - Apple Puree",
    description: "Pure organic apple puree for babies 6+ months. Made with certified organic apples.",
    category: "Baby Food",
    price: 4.99,
    inventory: 50,
    image_url: "/organic-baby-food-jar.jpg",
    status: "Active",
  },
  {
    id: "prod_002",
    seller_id: "me",
    title: "Wireless Bluetooth Headphones",
    description: "High-quality wireless headphones with noise cancellation.",
    category: "Electronics",
    price: 89.99,
    inventory: 25,
    image_url: "/wireless-bluetooth-headphones.jpg",
    status: "Flagged",
  },
  {
    id: "prod_003",
    seller_id: "seller_123",
    title: "Natural Pain Relief Cream",
    description: "Herbal pain relief cream with natural ingredients.",
    category: "Health",
    price: 19.99,
    inventory: 100,
    image_url: "/pain-relief-cream-tube.jpg",
    status: "Banned",
  },
  {
    id: "prod_004",
    seller_id: "me",
    title: "Kids Safety Helmet",
    description: "Protective helmet for children cycling and skating.",
    category: "Sports",
    price: 29.99,
    inventory: 15,
    image_url: "/kids-safety-helmet.jpg",
    status: "Active",
  },
  {
    id: "prod_005",
    seller_id: "seller_456",
    title: "Dietary Supplement - Vitamin D",
    description: "High-potency vitamin D supplement for daily health.",
    category: "Supplements",
    price: 15.99,
    inventory: 200,
    image_url: "/vitamin-d-supplement-bottle.jpg",
    status: "Flagged",
  },
  {
    id: "prod_006",
    seller_id: "me",
    title: "Eco-Friendly Water Bottle",
    description: "Reusable water bottle made from recycled materials.",
    category: "Home",
    price: 12.99,
    inventory: 75,
    image_url: "/eco-friendly-water-bottle.jpg",
    status: "Active",
  },
  {
    id: "prod_007",
    seller_id: "seller_789",
    title: "Smart Home Security Camera",
    description: "WiFi-enabled security camera with night vision.",
    category: "Electronics",
    price: 149.99,
    inventory: 30,
    image_url: "/smart-security-camera.jpg",
    status: "Active",
  },
  {
    id: "prod_008",
    seller_id: "seller_123",
    title: "Prescription Glasses Frames",
    description: "Designer prescription glasses frames.",
    category: "Health",
    price: 199.99,
    inventory: 10,
    image_url: "/prescription-glasses-frames.jpg",
    status: "Banned",
  },
]

function setupDatabase() {
  console.log("Setting up RegWatch AI database...")

  db.serialize(() => {
    // Clear existing data
    db.run("DELETE FROM compliance_results")
    db.run("DELETE FROM appeals")
    db.run("DELETE FROM flags")
    db.run("DELETE FROM products")

    // Insert sample products
    const insertProduct = db.prepare(`
      INSERT INTO products (id, seller_id, title, description, category, price, inventory, image_url, status, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    `)

    sampleProducts.forEach((product) => {
      insertProduct.run([
        product.id,
        product.seller_id,
        product.title,
        product.description,
        product.category,
        product.price,
        product.inventory,
        product.image_url,
        product.status,
      ])
    })

    insertProduct.finalize()

    // Add sample compliance results
    const complianceResults = [
      {
        product_id: "prod_002",
        compliant: false,
        violations: ["Missing FCC certification", "Incomplete safety warnings"],
        suggestions: ["Obtain FCC certification", "Add proper safety warnings"],
        severity: "medium",
        confidence: 0.8,
      },
      {
        product_id: "prod_003",
        compliant: false,
        violations: ["Unapproved medical claims", "Missing FDA approval"],
        suggestions: ["Remove medical claims", "Obtain FDA approval"],
        severity: "critical",
        confidence: 0.95,
      },
      {
        product_id: "prod_005",
        compliant: false,
        violations: ["Exceeds daily recommended dose", "Missing supplement facts"],
        suggestions: ["Adjust dosage", "Add supplement facts panel"],
        severity: "high",
        confidence: 0.85,
      },
    ]

    const insertCompliance = db.prepare(`
      INSERT INTO compliance_results (id, product_id, compliant, violations, suggestions, severity, confidence, uses_context, top_rules, agent_summaries, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    `)

    complianceResults.forEach((result, index) => {
      insertCompliance.run([
        `comp_${index + 1}`,
        result.product_id,
        result.compliant,
        JSON.stringify(result.violations),
        JSON.stringify(result.suggestions),
        result.severity,
        result.confidence,
        true,
        JSON.stringify(["FDA regulations", "Safety standards"]),
        JSON.stringify([
          {
            agent: "FDA_Drug_Agent",
            table: "drug_regulations",
            score: 0.3,
            compliant: false,
            severity: result.severity,
            uses_context: true,
            top_rules: result.violations,
          },
        ]),
      ])
    })

    insertCompliance.finalize()

    // Add sample flags
    const flags = [
      {
        id: "flag_001",
        listing_id: "prod_002",
        seller_id: "me",
        severity: "medium",
        reason: "Missing FCC certification",
      },
      {
        id: "flag_002",
        listing_id: "prod_003",
        seller_id: "seller_123",
        severity: "critical",
        reason: "Unapproved medical claims",
      },
      {
        id: "flag_003",
        listing_id: "prod_005",
        seller_id: "seller_456",
        severity: "high",
        reason: "Exceeds daily recommended dose",
      },
    ]

    const insertFlag = db.prepare(`
      INSERT INTO flags (id, listing_id, seller_id, severity, reason, created_at)
      VALUES (?, ?, ?, ?, ?, datetime('now'))
    `)

    flags.forEach((flag) => {
      insertFlag.run([flag.id, flag.listing_id, flag.seller_id, flag.severity, flag.reason])
    })

    insertFlag.finalize()

    console.log("Database setup completed successfully!")
    console.log(`- ${sampleProducts.length} sample products added`)
    console.log(`- ${complianceResults.length} compliance results added`)
    console.log(`- ${flags.length} flags added`)
  })

  db.close()
}

setupDatabase()
