"use client"

import Image from "next/image"
import { Card, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { StatusBadge } from "@/components/status-badge"
import { ScoreMeter } from "@/components/score-meter"
import type { Listing } from "@/lib/types"
import { Eye, Edit } from "lucide-react"

interface ListingCardProps {
  listing: Listing
  onView?: (listing: Listing) => void
  onEdit?: (listing: Listing) => void
  showActions?: boolean
}

export function ListingCard({ listing, onView, onEdit, showActions = false }: ListingCardProps) {
  const complianceScore = listing.compliance
    ? Math.round(
        100 *
          Math.max(listing.compliance.confidence, Math.max(...listing.compliance.agent_summaries.map((a) => a.score))),
      )
    : null

  return (
    <Card className="group hover:shadow-lg transition-shadow duration-200">
      <CardContent className="p-4">
        <div className="aspect-square relative mb-3 overflow-hidden rounded-lg bg-muted">
          <Image
            src={listing.image_url || "/placeholder.svg?height=200&width=200"}
            alt={listing.title}
            fill
            className="object-cover group-hover:scale-105 transition-transform duration-200"
          />
          <div className="absolute top-2 right-2">
            <StatusBadge status={listing.status} />
          </div>
          {complianceScore !== null && (
            <div className="absolute top-2 left-2">
              <ScoreMeter score={complianceScore} size="sm" />
            </div>
          )}
        </div>

        <div className="space-y-2">
          <h3 className="font-semibold text-sm line-clamp-2 text-balance">{listing.title}</h3>

          <div className="flex items-center justify-between">
            {listing.price && <span className="font-bold text-lg">${listing.price.toFixed(2)}</span>}
            {listing.category && (
              <Badge variant="outline" className="text-xs">
                {listing.category}
              </Badge>
            )}
          </div>

          {listing.compliance && !listing.compliance.compliant && (
            <div className="text-xs text-muted-foreground">
              <Badge variant="secondary" className="text-xs">
                {listing.compliance.severity}
              </Badge>
              <span className="ml-2">
                {listing.compliance.violations.length} violation{listing.compliance.violations.length !== 1 ? "s" : ""}
              </span>
            </div>
          )}
        </div>
      </CardContent>

      {showActions && (
        <CardFooter className="p-4 pt-0 flex gap-2">
          <Button variant="outline" size="sm" onClick={() => onView?.(listing)} className="flex-1">
            <Eye className="h-4 w-4 mr-1" />
            View
          </Button>
          <Button variant="outline" size="sm" onClick={() => onEdit?.(listing)} className="flex-1">
            <Edit className="h-4 w-4 mr-1" />
            Edit
          </Button>
        </CardFooter>
      )}
    </Card>
  )
}
