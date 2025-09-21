import { Badge } from "@/components/ui/badge"
import type { ListingStatus } from "@/lib/types"

interface StatusBadgeProps {
  status: ListingStatus
  className?: string
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const variants = {
    Active: { variant: "default" as const, color: "text-green-600 bg-green-50 dark:bg-green-950 dark:text-green-400" },
    Flagged: {
      variant: "secondary" as const,
      color: "text-yellow-600 bg-yellow-50 dark:bg-yellow-950 dark:text-yellow-400",
    },
    Banned: { variant: "destructive" as const, color: "text-red-600 bg-red-50 dark:bg-red-950 dark:text-red-400" },
  }

  const config = variants[status]

  return (
    <Badge variant={config.variant} className={`${config.color} ${className}`}>
      {status}
    </Badge>
  )
}
