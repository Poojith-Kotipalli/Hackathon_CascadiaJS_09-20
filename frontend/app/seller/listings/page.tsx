"use client"

import { useState, useEffect } from "react"
import { Navigation } from "@/components/navigation"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { StatusBadge } from "@/components/status-badge"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/hooks/use-toast"
import { apiClient } from "@/lib/api"
import type { Listing } from "@/lib/types"
import { useSearchParams } from "next/navigation"
import { Loader2, RefreshCw, Edit, AlertTriangle } from "lucide-react"
import { formatDistanceToNow } from "date-fns"

export default function MyListingsPage() {
  const [listings, setListings] = useState<Listing[]>([])
  const [loading, setLoading] = useState(true)
  const [recheckingIds, setRecheckingIds] = useState<Set<string>>(new Set())
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()

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
        // Mock data for seller's listings
        const mockListings: Listing[] = [
          {
            id: "prod_001",
            seller_id: "me",
            title: "Organic Baby Food - Apple Puree",
            description: "Pure organic apple puree for babies 6+ months.",
            category: "Baby Food",
            price: 4.99,
            inventory: 50,
            image_url: "/organic-baby-food-jar.jpg",
            status: "Active",
            last_checked_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
            updated_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
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
            last_checked_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
            created_at: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
            updated_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
            compliance: {
              compliant: false,
              violations: ["Missing FCC certification"],
              suggestions: ["Obtain FCC certification"],
              severity: "medium",
              confidence: 0.8,
              uses_context: true,
              top_rules: ["FCC regulations"],
              agent_summaries: [],
            },
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
            last_checked_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
            created_at: new Date(Date.now() - 72 * 60 * 60 * 1000).toISOString(),
            updated_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
          },
        ]
        setListings(mockListings)
      } else {
        const data = await apiClient.getProducts("me")
        setListings(data)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load listings")
    } finally {
      setLoading(false)
    }
  }

  const handleRecheck = async (listingId: string) => {
    setRecheckingIds((prev) => new Set(prev).add(listingId))

    try {
      if (isMockMode) {
        // Mock recheck
        await new Promise((resolve) => setTimeout(resolve, 2000))
        toast({
          title: "Compliance check completed",
          description: "Your listing has been re-scanned for compliance.",
        })
        // Refresh listings
        await loadListings()
      } else {
        await apiClient.recheckProduct(listingId)
        toast({
          title: "Compliance check queued",
          description: "Your listing will be re-scanned for compliance.",
        })
      }
    } catch (error) {
      toast({
        title: "Error rechecking listing",
        description: error instanceof Error ? error.message : "Please try again.",
        variant: "destructive",
      })
    } finally {
      setRecheckingIds((prev) => {
        const newSet = new Set(prev)
        newSet.delete(listingId)
        return newSet
      })
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="container py-8 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="container py-8">
          <div className="text-center">
            <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Error Loading Listings</h2>
            <p className="text-muted-foreground mb-4">{error}</p>
            <Button onClick={loadListings}>Try Again</Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="container py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold">My Listings</h1>
            <p className="text-muted-foreground">Manage your product listings and compliance status</p>
          </div>
          <Button onClick={loadListings} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>

        {listings.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground mb-4">You haven't created any listings yet.</p>
            <Button asChild>
              <a href="/sell">Create Your First Listing</a>
            </Button>
          </div>
        ) : (
          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Product</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Price</TableHead>
                  <TableHead>Last Checked</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {listings.map((listing) => (
                  <TableRow key={listing.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-lg overflow-hidden bg-muted flex-shrink-0">
                          <img
                            src={listing.image_url || "/placeholder.svg?height=48&width=48"}
                            alt={listing.title}
                            className="w-full h-full object-cover"
                          />
                        </div>
                        <div className="min-w-0">
                          <p className="font-medium truncate">{listing.title}</p>
                          {listing.category && (
                            <Badge variant="outline" className="text-xs mt-1">
                              {listing.category}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={listing.status} />
                      {listing.compliance && !listing.compliance.compliant && (
                        <div className="mt-1">
                          <Badge variant="secondary" className="text-xs">
                            {listing.compliance.violations.length} violation
                            {listing.compliance.violations.length !== 1 ? "s" : ""}
                          </Badge>
                        </div>
                      )}
                    </TableCell>
                    <TableCell>{listing.price ? `$${listing.price.toFixed(2)}` : "—"}</TableCell>
                    <TableCell>
                      {listing.last_checked_at ? (
                        <span className="text-sm text-muted-foreground">
                          {formatDistanceToNow(new Date(listing.last_checked_at), { addSuffix: true })}
                        </span>
                      ) : (
                        <span className="text-sm text-muted-foreground">Never</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleRecheck(listing.id)}
                          disabled={recheckingIds.has(listing.id)}
                        >
                          {recheckingIds.has(listing.id) ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <RefreshCw className="h-4 w-4" />
                          )}
                          <span className="sr-only">Re-check</span>
                        </Button>
                        <Button variant="outline" size="sm">
                          <Edit className="h-4 w-4" />
                          <span className="sr-only">Edit</span>
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </main>
    </div>
  )
}
