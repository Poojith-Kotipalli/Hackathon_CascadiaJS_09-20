"use client"

import { useState, useEffect } from "react"
import { Navigation } from "@/components/navigation"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { FlagsTab } from "@/components/console/flags-tab"
import { AppealsTab } from "@/components/console/appeals-tab"
import { BannedTab } from "@/components/console/banned-tab"
import { Badge } from "@/components/ui/badge"
import { useSearchParams } from "next/navigation"
import { apiClient } from "@/lib/api"
import type { Flag, Appeal, Listing } from "@/lib/types"
import { Loader2, Shield } from "lucide-react"

export default function ConsolePage() {
  const [flags, setFlags] = useState<Flag[]>([])
  const [appeals, setAppeals] = useState<Appeal[]>([])
  const [bannedListings, setBannedListings] = useState<Listing[]>([])
  const [loading, setLoading] = useState(true)

  const searchParams = useSearchParams()
  const isMockMode = searchParams.get("mock") === "1"

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)

      if (isMockMode) {
        // Mock data for compliance console
        const mockFlags: Flag[] = [
          {
            id: "flag_001",
            listing_id: "prod_002",
            seller_id: "me",
            severity: "medium",
            reason: "Missing FCC certification, Incomplete safety warnings",
            reviewed: false,
            created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          },
          {
            id: "flag_002",
            listing_id: "prod_005",
            seller_id: "seller_456",
            severity: "high",
            reason: "Exceeds daily recommended dose, Missing supplement facts",
            reviewed: false,
            created_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
          },
          {
            id: "flag_003",
            listing_id: "prod_003",
            seller_id: "seller_123",
            severity: "critical",
            reason: "Unapproved medical claims, Missing FDA approval",
            reviewed: false,
            created_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
          },
        ]

        const mockAppeals: Appeal[] = [
          {
            id: "appeal_001",
            listing_id: "prod_002",
            seller_id: "me",
            reason: "We have obtained FCC certification and updated our product listing with proper safety warnings.",
            status: "pending",
            created_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
          },
          {
            id: "appeal_002",
            listing_id: "prod_005",
            seller_id: "seller_456",
            reason: "The dosage has been corrected and supplement facts panel has been added to the product packaging.",
            status: "pending",
            created_at: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
          },
        ]

        const mockBannedListings: Listing[] = [
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
            created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
            updated_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
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
            created_at: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
            updated_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
          },
        ]

        setFlags(mockFlags)
        setAppeals(mockAppeals)
        setBannedListings(mockBannedListings)
      } else {
        const [flagsData, appealsData, productsData] = await Promise.all([
          apiClient.getFlags(),
          apiClient.getAppeals(),
          apiClient.getProducts(),
        ])

        setFlags(flagsData)
        setAppeals(appealsData)
        setBannedListings(productsData.filter((p: Listing) => p.status === "Banned"))
      }
    } catch (error) {
      console.error("Error loading console data:", error)
    } finally {
      setLoading(false)
    }
  }

  const pendingFlags = flags.filter((f) => !f.reviewed)
  const pendingAppeals = appeals.filter((a) => a.status === "pending")

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

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="container py-8">
        <div className="flex items-center gap-3 mb-6">
          <Shield className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-3xl font-bold">Compliance Console</h1>
            <p className="text-muted-foreground">Monitor and manage regulatory compliance across the marketplace</p>
          </div>
        </div>

        <Tabs defaultValue="flags" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="flags" className="flex items-center gap-2">
              Flags
              {pendingFlags.length > 0 && (
                <Badge variant="destructive" className="ml-1">
                  {pendingFlags.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="appeals" className="flex items-center gap-2">
              Appeals
              {pendingAppeals.length > 0 && (
                <Badge variant="secondary" className="ml-1">
                  {pendingAppeals.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="banned">Banned ({bannedListings.length})</TabsTrigger>
          </TabsList>

          <TabsContent value="flags">
            <FlagsTab flags={flags} onRefresh={loadData} isMockMode={isMockMode} />
          </TabsContent>

          <TabsContent value="appeals">
            <AppealsTab appeals={appeals} onRefresh={loadData} isMockMode={isMockMode} />
          </TabsContent>

          <TabsContent value="banned">
            <BannedTab listings={bannedListings} onRefresh={loadData} isMockMode={isMockMode} />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
