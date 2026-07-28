import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ArrowRight, Zap, Clock, Shield } from "lucide-react"

const recommendations = [
  {
    title: "Rightsizing EC2",
    description: "15 instâncias subutilizadas identificadas",
    savings: 2400,
    impact: "alto",
    icon: Zap,
  },
  {
    title: "Reserved Instances",
    description: "Converter 8 instâncias On-Demand",
    savings: 1800,
    impact: "alto",
    icon: Shield,
  },
  {
    title: "Snapshots Antigos",
    description: "42 snapshots com mais de 90 dias",
    savings: 350,
    impact: "baixo",
    icon: Clock,
  },
]

export function Recommendations() {
  return (
    <div className="p-6 bg-card rounded-xl border border-border">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-card-foreground">
            Recomendações de Otimização
          </h3>
          <p className="text-sm text-muted-foreground">
            Economia potencial: $4.550/mês
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {recommendations.map((rec) => (
          <div
            key={rec.title}
            className="flex items-center justify-between p-4 rounded-lg border border-border hover:border-primary/50 transition-colors"
          >
            <div className="flex items-center gap-4">
              <div className="p-2 rounded-lg bg-primary/10">
                <rec.icon className="w-5 h-5 text-primary" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-card-foreground">
                    {rec.title}
                  </p>
                  <Badge
                    variant={rec.impact === "alto" ? "default" : "secondary"}
                    className="text-xs"
                  >
                    {rec.impact}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">{rec.description}</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm font-semibold text-chart-3">
                  -${rec.savings.toLocaleString()}/mês
                </p>
              </div>
              <Button variant="ghost" size="icon">
                <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
