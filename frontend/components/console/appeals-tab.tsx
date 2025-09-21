"use client"

import { useState } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useToast } from "@/hooks/use-toast"
import { apiClient } from "@/lib/api"
import type { Appeal } from "@/lib/types"
import { formatDistanceToNow } from "date-fns"
import { CheckCircle, X, Loader2, MessageSquare } from "lucide-react"

interface AppealsTabProps {
  appeals: Appeal[]
  onRefresh: () => void
  isMockMode: boolean
}

export function AppealsTab({ appeals, onRefresh, isMockMode }: AppealsTabProps) {
  const [processingIds, setProcessingIds] = useState<Set<string>>(new Set())
  const { toast } = useToast()

  const handleResolveAppeal = async (appeal: Appeal, approve: boolean) => {
    setProcessingIds((prev) => new Set(prev).add(appeal.id))

    try {
      if (isMockMode) {
        await new Promise((resolve) => setTimeout(resolve, 1000))
        toast({
          title: approve ? "Appeal approved" : "Appeal rejected",
          description: approve
            ? "The listing has been reinstated to the marketplace."
            : "The appeal has been rejected and the listing remains banned.",
        })
      } else {
        await apiClient.resolveAppeal(appeal.id, approve)
        toast({
          title: approve ? "Appeal approved successfully" : "Appeal rejected",
          description: approve
            ? "The listing has been reinstated to the marketplace."
            : "The appeal has been rejected.",
        })
      }
      onRefresh()
    } catch (error) {
      toast({
        title: "Error resolving appeal",
        description: error instanceof Error ? error.message : "Please try again.",
        variant: "destructive",
      })
    } finally {
      setProcessingIds((prev) => {
        const newSet = new Set(prev)
        newSet.delete(appeal.id)
        return newSet
      })
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "approved":
        return "default"
      case "rejected":
        return "destructive"
      case "pending":
        return "secondary"
      default:
        return "outline"
    }
  }

  const pendingAppeals = appeals.filter((a) => a.status === "pending")
  const resolvedAppeals = appeals.filter((a) => a.status !== "pending")

  return (
    <div className="space-y-6">
      {/* Pending Appeals */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-blue-500" />
            Pending Appeals ({pendingAppeals.length})
          </CardTitle>
          <CardDescription>Review seller appeals for banned or flagged listings.</CardDescription>
        </CardHeader>
        <CardContent>
          {pendingAppeals.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">No pending appeals to review.</div>
          ) : (
            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Listing</TableHead>
                    <TableHead>Seller</TableHead>
                    <TableHead>Appeal Reason</TableHead>
                    <TableHead>Submitted</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {pendingAppeals.map((appeal) => (
                    <TableRow key={appeal.id}>
                      <TableCell>
                        <div className="font-medium">Listing #{appeal.listing_id.slice(-6)}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{appeal.seller_id}</Badge>
                      </TableCell>
                      <TableCell>
                        <div className="max-w-md">
                          <p className="text-sm text-muted-foreground line-clamp-3">{appeal.reason}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-muted-foreground">
                          {formatDistanceToNow(new Date(appeal.created_at), { addSuffix: true })}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="default"
                            size="sm"
                            onClick={() => handleResolveAppeal(appeal, true)}
                            disabled={processingIds.has(appeal.id)}
                          >
                            {processingIds.has(appeal.id) ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <CheckCircle className="h-4 w-4" />
                            )}
                            Approve
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => handleResolveAppeal(appeal, false)}
                            disabled={processingIds.has(appeal.id)}
                          >
                            {processingIds.has(appeal.id) ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <X className="h-4 w-4" />
                            )}
                            Reject
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Resolved Appeals */}
      {resolvedAppeals.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Resolved Appeals ({resolvedAppeals.length})</CardTitle>
            <CardDescription>Previously resolved appeals for reference.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Listing</TableHead>
                    <TableHead>Seller</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Resolved</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {resolvedAppeals.slice(0, 10).map((appeal) => (
                    <TableRow key={appeal.id}>
                      <TableCell>
                        <div className="font-medium">Listing #{appeal.listing_id.slice(-6)}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{appeal.seller_id}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusColor(appeal.status) as any}>{appeal.status}</Badge>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-muted-foreground">
                          {appeal.resolved_at
                            ? formatDistanceToNow(new Date(appeal.resolved_at), { addSuffix: true })
                            : "—"}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
