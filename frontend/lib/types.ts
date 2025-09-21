export type Severity = "critical" | "high" | "medium" | "low"
export type ListingStatus = "Active" | "Flagged" | "Banned"

export type AgentSummary = {
  agent: "CPSC_Safety_Agent" | "FDA_Drug_Agent" | "FDA_Food_Agent" | "FDA_Device_Agent"
  table: string
  score: number
  compliant: boolean
  severity: Severity
  uses_context: boolean
  top_rules: string[]
}

export type ComplianceResponse = {
  compliant: boolean
  violations: string[]
  suggestions: string[]
  severity: Severity
  confidence: number
  uses_context: boolean
  top_rules: string[]
  agent_summaries: AgentSummary[]
}

export type Listing = {
  id: string
  seller_id: string
  title: string
  description: string
  category?: string
  price?: number
  inventory?: number
  image_url?: string
  status: ListingStatus
  last_checked_at?: string
  created_at: string
  updated_at: string
  compliance?: ComplianceResponse
}

export type Flag = {
  id: string
  listing_id: string
  seller_id: string
  severity: Severity
  reason: string
  created_at: string
  reviewed: boolean
}

export type Appeal = {
  id: string
  listing_id: string
  seller_id: string
  reason: string
  status: "pending" | "approved" | "rejected"
  created_at: string
  resolved_at?: string
}
