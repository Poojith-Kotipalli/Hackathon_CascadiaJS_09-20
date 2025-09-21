"use client"

import { useState, useEffect } from "react"
import { Navigation } from "@/components/navigation"
import { ListingCard } from "@/components/listing-card"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { Badge } from "@/components/ui/badge"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { ScoreMeter } from "@/components/score-meter"
import { StatusBadge } from "@/components/status-badge"
import type { Listing } from "@/lib/types"
import { apiClient } from "@/lib/api"
import { useSearchParams } from "next/navigation"
import { Loader2, AlertTriangle, CheckCircle } from "lucide-react"

export default function ProductsPage() {
  const [listings, setListings] = useState<Listing[]>([])
  const [filteredListings, setFilteredListings] = useState<Listing[]>([])
  const [selectedListing, setSelectedListing] = useState<Listing | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const searchParams = useSearchParams()
  const isMockMode = searchParams.get("mock") === "1"

  useEffect(() => {
    loadListings()
  }, [])

  const loadListings = async () => {
    try {
      setLoading(true)
      setError(null)

      if (isMockMode) {
        // Mock data for offline mode
        const mockListings: Listing[] = [
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
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
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
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            compliance: {
              compliant: false,
              violations: ["Missing FCC certification", "Incomplete safety warnings"],
              suggestions: ["Obtain FCC certification", "Add proper safety warnings"],
              severity: "medium",
              confidence: 0.8,
              uses_context: true,
              top_rules: ["FCC regulations", "Safety standards"],
              agent_summaries: [
                {
                  agent: "CPSC_Safety_Agent",
                  table: "electronics_safety",
                  score: 0.6,
                  compliant: false,
                  severity: "medium",
                  uses_context: true,
                  top_rules: ["FCC certification required", "Safety warnings mandatory"],
                },
              ],
            },
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
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            compliance: {
              compliant: false,
              violations: ["Unapproved medical claims", "Missing FDA approval"],
              suggestions: ["Remove medical claims", "Obtain FDA approval"],
              severity: "critical",
              confidence: 0.95,
              uses_context: true,
              top_rules: ["FDA drug regulations", "Medical claims restrictions"],
              agent_summaries: [
                {
                  agent: "FDA_Drug_Agent",
                  table: "drug_regulations",
                  score: 0.2,
                  compliant: false,
                  severity: "critical",
                  uses_context: true,
                  top_rules: ["FDA approval required", "Medical claims prohibited"],
                },
              ],
            },
          },
        ]
        setListings(mockListings)
        setFilteredListings(mockListings)
      } else {
        const data = await apiClient.getProducts()
        setListings(data)
        setFilteredListings(data)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load listings")
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (query: string) => {
    if (!query.trim()) {
      setFilteredListings(listings)
      return
    }

    const filtered = listings.filter(
      (listing) =>
        listing.title.toLowerCase().includes(query.toLowerCase()) ||
        listing.description.toLowerCase().includes(query.toLowerCase()) ||
        listing.category?.toLowerCase().includes(query.toLowerCase()),
    )
    setFilteredListings(filtered)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation onSearch={handleSearch} />
        <div className="container py-8 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation onSearch={handleSearch} />
        <div className="container py-8">
          <div className="text-center">
            <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Error Loading Products</h2>
            <p className="text-muted-foreground mb-4">{error}</p>
            <Button onClick={loadListings}>Try Again</Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation onSearch={handleSearch} />

      <main className="container py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-balance">Marketplace</h1>
            <p className="text-muted-foreground">
              {filteredListings.length} product{filteredListings.length !== 1 ? "s" : ""} available
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredListings.map((listing) => (
            <ListingCard key={listing.id} listing={listing} onView={setSelectedListing} />
          ))}
        </div>

        {filteredListings.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No products found matching your search.</p>
          </div>
        )}
      </main>

      {/* Listing Detail Sheet */}
      <Sheet open={!!selectedListing} onOpenChange={() => setSelectedListing(null)}>
        <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
          {selectedListing && (
            <>
              <SheetHeader>
                <SheetTitle className="text-balance">{selectedListing.title}</SheetTitle>
              </SheetHeader>

              <div className="mt-6 space-y-6">
                <div className="aspect-square relative rounded-lg overflow-hidden bg-muted">
                  <img
                    src={selectedListing.image_url || "/placeholder.svg?height=400&width=400"}
                    alt={selectedListing.title}
                    className="w-full h-full object-cover"
                  />
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <StatusBadge status={selectedListing.status} />
                    {selectedListing.price && (
                      <span className="text-2xl font-bold">${selectedListing.price.toFixed(2)}</span>
                    )}
                  </div>

                  <p className="text-muted-foreground text-pretty">{selectedListing.description}</p>

                  {selectedListing.category && (
                    <div>
                      <Badge variant="outline">{selectedListing.category}</Badge>
                    </div>
                  )}

                  {selectedListing.compliance && (
                    <div className="border rounded-lg p-4 space-y-4">
                      <div className="flex items-center justify-between">
                        <h3 className="font-semibold">Compliance Status</h3>
                        <ScoreMeter
                          score={Math.round(
                            100 *
                              Math.max(
                                selectedListing.compliance.confidence,
                                Math.max(...selectedListing.compliance.agent_summaries.map((a) => a.score)),
                              ),
                          )}
                        />
                      </div>

                      <div className="flex items-center gap-2">
                        {selectedListing.compliance.compliant ? (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        ) : (
                          <AlertTriangle className="h-4 w-4 text-red-500" />
                        )}
                        <Badge variant={selectedListing.compliance.compliant ? "default" : "destructive"}>
                          {selectedListing.compliance.severity}
                        </Badge>
                        {selectedListing.compliance.uses_context && (
                          <Badge variant="outline" className="text-xs">
                            Uses Context
                          </Badge>
                        )}
                      </div>

                      {selectedListing.compliance.violations.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-2">Violations</h4>
                          <div className="space-y-1">
                            {selectedListing.compliance.violations.map((violation, index) => (
                              <Badge key={index} variant="destructive" className="mr-1 mb-1">
                                {violation}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {selectedListing.compliance.suggestions.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-2">Suggestions</h4>
                          <div className="space-y-1">
                            {selectedListing.compliance.suggestions.map((suggestion, index) => (
                              <Badge key={index} variant="secondary" className="mr-1 mb-1">
                                {suggestion}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      <Accordion type="single" collapsible>
                        <AccordionItem value="agents">
                          <AccordionTrigger>Agent Analysis</AccordionTrigger>
                          <AccordionContent>
                            <div className="space-y-3">
                              {selectedListing.compliance.agent_summaries.map((agent, index) => (
                                <div key={index} className="border rounded p-3 space-y-2">
                                  <div className="flex items-center justify-between">
                                    <span className="font-medium text-sm">{agent.agent}</span>
                                    <ScoreMeter score={Math.round(agent.score * 100)} size="sm" />
                                  </div>
                                  <div className="text-xs text-muted-foreground">Table: {agent.table}</div>
                                  <div className="flex items-center gap-2">
                                    <Badge variant={agent.compliant ? "default" : "destructive"} className="text-xs">
                                      {agent.severity}
                                    </Badge>
                                    {agent.uses_context && (
                                      <Badge variant="outline" className="text-xs">
                                        Context
                                      </Badge>
                                    )}
                                  </div>
                                  <div className="text-xs">
                                    <strong>Top Rules:</strong> {agent.top_rules.slice(0, 2).join(", ")}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </AccordionContent>
                        </AccordionItem>
                      </Accordion>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  )
}
