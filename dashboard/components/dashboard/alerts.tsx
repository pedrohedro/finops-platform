import { AlertTriangle, TrendingUp, Clock } from "lucide-react"
import { cn } from "@/lib/utils"

const alerts = [
  {
    title: "Limite de orçamento atingido",
    description: "EC2 ultrapassou 90% do orçamento mensal",
    time: "2 min atrás",
    type: "warning",
    icon: AlertTriangle,
  },
  {
    title: "Aumento de custo detectado",
    description: "Lambda aumentou 45% nas últimas 24h",
    time: "1 hora atrás",
    type: "error",
    icon: TrendingUp,
  },
  {
    title: "Reserva expirando",
    description: "3 Reserved Instances expiram em 7 dias",
    time: "3 horas atrás",
    type: "info",
    icon: Clock,
  },
]

export function Alerts() {
  return (
    <div className="p-6 bg-card rounded-xl border border-border">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-card-foreground">
            Alertas Recentes
          </h3>
          <p className="text-sm text-muted-foreground">3 alertas ativos</p>
        </div>
        <button className="text-sm text-primary hover:underline">Ver todos</button>
      </div>

      <div className="space-y-3">
        {alerts.map((alert, index) => (
          <div
            key={index}
            className={cn(
              "flex items-start gap-3 p-3 rounded-lg border",
              alert.type === "warning" && "border-accent/50 bg-accent/5",
              alert.type === "error" && "border-destructive/50 bg-destructive/5",
              alert.type === "info" && "border-primary/50 bg-primary/5"
            )}
          >
            <div
              className={cn(
                "p-2 rounded-lg",
                alert.type === "warning" && "bg-accent/20",
                alert.type === "error" && "bg-destructive/20",
                alert.type === "info" && "bg-primary/20"
              )}
            >
              <alert.icon
                className={cn(
                  "w-4 h-4",
                  alert.type === "warning" && "text-accent",
                  alert.type === "error" && "text-destructive",
                  alert.type === "info" && "text-primary"
                )}
              />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-card-foreground">
                {alert.title}
              </p>
              <p className="text-sm text-muted-foreground">{alert.description}</p>
              <p className="text-xs text-muted-foreground mt-1">{alert.time}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
