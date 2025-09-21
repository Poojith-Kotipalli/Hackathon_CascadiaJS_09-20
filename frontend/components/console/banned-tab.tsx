"use client"

import { useState } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useToast } from "@/hooks/use-toast"
import { apiClient } from "@/lib/api"
import type { Listing } from "@/lib/types"
import { formatDistanceToNow } from "date-fns"
import { RotateCcw, Loader2, Ban } from "lucide-react"

interface BannedTabProps {
  listings: Listing[]
  onRefresh: () => void
  isMockMode: boolean
}

export function BannedTab({ listings, onRefresh, isMockMode }: BannedTabProps) {
  const [processingIds, setProcessingIds] = useState<Set<string>>(new Set())
  const { toast } = useToast()

  const handleReinstate = async (listing: Listing) => {
    setProcessingIds((prev) => new Set(prev).add(listing.id))

    try {
      if (isMockMode) {
        await new Promise((resolve) => setTimeout(resolve, 1000))
        toast({
          title: "Product reinstated",
          description: "The listing has been reinstated and is now active in the marketplace.",
        })
      } else {
        await apiClient.reinstateProduct(listing.id)
        toast({
          title: "Product reinstated successfully",
          description: "The listing has been reinstated and is now active in the marketplace.",
        })
      }
      onRefresh()
    } catch (error) {
      toast({
        title: "Error reinstating product",
        description: error instanceof Error ? error.message : "Please try again.",
        variant: "destructive",
      })
    } finally {
      setProcessingIds((prev) => {
        const newSet = new Set(prev)
        newSet.delete(listing.id)
        return newSet
      })
    }
  }

  if (listings.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Ban className="h-5 w-5 text-red-500" />
            No Banned Products
          </CardTitle>
          <CardDescription>No products are currently banned from the marketplace.</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Ban className="h-5 w-5 text-red-500" />
          Banned Products ({listings.length})
        </CardTitle>
        <CardDescription>Manage products that have been banned from the marketplace.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="border rounded-lg">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Product</TableHead>
                <TableHead>Seller</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Banned</TableHead>
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
                        {listing.price && <p className="text-sm text-muted-foreground">${listing.price.toFixed(2)}</p>}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{listing.seller_id}</Badge>
                  </TableCell>
                  <TableCell>
                    {listing.category && (
                      <Badge variant="secondary" className="text-xs">
                        {listing.category}
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <span className="text-sm text-muted-foreground">
                      {formatDistanceToNow(new Date(listing.updated_at), { addSuffix: true })}
                    </span>
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleReinstate(listing)}
                      disabled={processingIds.has(listing.id)}
                    >
                      {processingIds.has(listing.id) ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <RotateCcw className="h-4 w-4" />
                      )}
                      Reinstate
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}
