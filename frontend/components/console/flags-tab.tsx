"use client"

import { useState } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useToast } from "@/hooks/use-toast"
import { apiClient } from "@/lib/api"
import type { Flag } from "@/lib/types"
import { formatDistanceToNow } from "date-fns"
import { Ban, CheckCircle, Loader2, AlertTriangle } from "lucide-react"

interface FlagsTabProps {
  flags: Flag[]
  onRefresh: () => void
  isMockMode: boolean
}

export function FlagsTab({ flags, onRefresh, isMockMode }: FlagsTabProps) {
  const [processingIds, setProcessingIds] = useState<Set<string>>(new Set())
  const { toast } = useToast()

  const handleBan = async (flag: Flag) => {
    setProcessingIds((prev) => new Set(prev).add(flag.id))

    try {
      if (isMockMode) {
        await new Promise((resolve) => setTimeout(resolve, 1000))
        toast({
          title: "Product banned",
          description: "The listing has been banned and removed from the marketplace.",
        })
      } else {
        await apiClient.banProduct(flag.listing_id, flag.reason)
        toast({
          title: "Product banned successfully",
          description: "The listing has been banned and removed from the marketplace.",
        })
      }
      onRefresh()
    } catch (error) {
      toast({
        title: "Error banning product",
        description: error instanceof Error ? error.message : "Please try again.",
        variant: "destructive",
      })
    } finally {
      setProcessingIds((prev) => {
        const newSet = new Set(prev)
        newSet.delete(flag.id)
        return newSet
      })
    }
  }

  const handleMarkReviewed = async (flag: Flag) => {
    setProcessingIds((prev) => new Set(prev).add(flag.id))

    try {
      if (isMockMode) {
        await new Promise((resolve) => setTimeout(resolve, 500))
        toast({
          title: "Flag marked as reviewed",
          description: "The flag has been marked as reviewed and will be hidden.",
        })
      } else {
        // In a real implementation, you'd have an API endpoint to mark flags as reviewed
        toast({
          title: "Flag marked as reviewed",
          description: "The flag has been marked as reviewed.",
        })
      }
      onRefresh()
    } catch (error) {
      toast({
        title: "Error updating flag",
        description: error instanceof Error ? error.message : "Please try again.",
        variant: "destructive",
      })
    } finally {
      setProcessingIds((prev) => {
        const newSet = new Set(prev)
        newSet.delete(flag.id)
        return newSet
      })
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "destructive"
      case "high":
        return "destructive"
      case "medium":
        return "secondary"
      case "low":
        return "outline"
      default:
        return "outline"
    }
  }

  const pendingFlags = flags.filter((f) => !f.reviewed)

  if (pendingFlags.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            No Pending Flags
          </CardTitle>
          <CardDescription>All compliance flags have been reviewed. Great work!</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-yellow-500" />
          Compliance Flags ({pendingFlags.length})
        </CardTitle>
        <CardDescription>
          Review and take action on flagged listings that violate regulatory requirements.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="border rounded-lg">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Listing</TableHead>
                <TableHead>Seller</TableHead>
                <TableHead>Severity</TableHead>
                <TableHead>Reason</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pendingFlags.map((flag) => (
                <TableRow key={flag.id}>
                  <TableCell>
                    <div className="font-medium">Listing #{flag.listing_id.slice(-6)}</div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{flag.seller_id}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={getSeverityColor(flag.severity) as any}>{flag.severity}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="max-w-xs">
                      <p className="text-sm text-muted-foreground line-clamp-2">{flag.reason}</p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm text-muted-foreground">
                      {formatDistanceToNow(new Date(flag.created_at), { addSuffix: true })}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleBan(flag)}
                        disabled={processingIds.has(flag.id)}
                      >
                        {processingIds.has(flag.id) ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Ban className="h-4 w-4" />
                        )}
                        Ban
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleMarkReviewed(flag)}
                        disabled={processingIds.has(flag.id)}
                      >
                        {processingIds.has(flag.id) ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <CheckCircle className="h-4 w-4" />
                        )}
                        Mark Reviewed
                      </Button>
                    </div>
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
