import { cn } from "@/lib/utils"
import { LucideIcon, TrendingUp, TrendingDown } from "lucide-react"

interface StatCardProps {
  title: string
  value: string
  change?: number
  changeLabel?: string
  icon: LucideIcon
  trend?: "up" | "down" | "neutral"
}

export function StatCard({
  title,
  value,
  change,
  changeLabel,
  icon: Icon,
  trend = "neutral",
}: StatCardProps) {
  return (
    <div className="p-6 bg-card rounded-xl border border-border">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="text-2xl font-semibold text-card-foreground">{value}</p>
          {change !== undefined && (
            <div className="flex items-center gap-1">
              {trend === "up" && (
                <TrendingUp className="w-4 h-4 text-destructive" />
              )}
              {trend === "down" && (
                <TrendingDown className="w-4 h-4 text-chart-3" />
              )}
              <span
                className={cn(
                  "text-sm font-medium",
                  trend === "up" && "text-destructive",
                  trend === "down" && "text-chart-3",
                  trend === "neutral" && "text-muted-foreground"
                )}
              >
                {change > 0 ? "+" : ""}
                {change}%
              </span>
              {changeLabel && (
                <span className="text-sm text-muted-foreground">
                  {changeLabel}
                </span>
              )}
            </div>
          )}
        </div>
        <div className="p-3 rounded-lg bg-secondary">
          <Icon className="w-5 h-5 text-primary" />
        </div>
      </div>
    </div>
  )
}
