import { Badge } from "@/components/ui/badge"
import { Server, Database, HardDrive, Cpu } from "lucide-react"

const SERVICE_ICONS: Record<string, typeof Server> = {
  EC2: Server,
  RDS: Database,
  S3: HardDrive,
  Lambda: Cpu,
}

const fallbackResources = [
  { name: "prod-api-cluster", type: "EC2", cost: 4250, change: 12, region: "us-east-1" },
  { name: "main-database", type: "RDS", cost: 3800, change: -5, region: "us-east-1" },
  { name: "analytics-cluster", type: "EC2", cost: 2900, change: 8, region: "us-west-2" },
  { name: "media-storage", type: "S3", cost: 2100, change: 25, region: "us-east-1" },
  { name: "cache-cluster", type: "ElastiCache", cost: 1800, change: -2, region: "us-east-1" },
]

interface TopResourcesProps {
  data?: Array<{
    date: string
    service: string
    team: string
    environment: string
    cost: number
    type: string
  }>
}

export function TopResources({ data }: TopResourcesProps) {
  let resources: Array<{ name: string; type: string; cost: number; region: string; change: number }>

  if (data && data.length > 0) {
    const aggregated = data.reduce((acc, item) => {
      const key = `${item.service}-${item.environment}`
      if (!acc[key]) {
        acc[key] = { name: item.service, type: item.service, cost: 0, region: item.environment, change: 0 }
      }
      acc[key].cost += item.cost
      return acc
    }, {} as Record<string, { name: string; type: string; cost: number; region: string; change: number }>)

    resources = Object.values(aggregated)
      .sort((a, b) => b.cost - a.cost)
      .slice(0, 5)
  } else {
    resources = fallbackResources
  }

  return (
    <div className="p-6 bg-card rounded-xl border border-border">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-card-foreground">
            Recursos Mais Caros
          </h3>
          <p className="text-sm text-muted-foreground">Top 5 este mes</p>
        </div>
        <button className="text-sm text-primary hover:underline">Ver todos</button>
      </div>

      <div className="space-y-4">
        {resources.map((resource) => {
          const Icon = SERVICE_ICONS[resource.type] || Server
          return (
            <div
              key={`${resource.name}-${resource.region}`}
              className="flex items-center justify-between p-3 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-secondary">
                  <Icon className="w-4 h-4 text-primary" />
                </div>
                <div>
                  <p className="text-sm font-medium text-card-foreground">
                    {resource.name}
                  </p>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="text-xs">
                      {resource.type}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {resource.region}
                    </span>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-semibold text-card-foreground">
                  ${resource.cost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
                {resource.change !== 0 && (
                  <p className={`text-xs ${resource.change > 0 ? "text-destructive" : "text-chart-3"}`}>
                    {resource.change > 0 ? "+" : ""}{resource.change}%
                  </p>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
