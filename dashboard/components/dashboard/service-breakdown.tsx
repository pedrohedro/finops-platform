"use client"

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts"

const COLORS = [
  "oklch(0.7 0.15 200)",
  "oklch(0.75 0.12 85)",
  "oklch(0.65 0.18 145)",
  "oklch(0.7 0.12 280)",
  "oklch(0.5 0 0)",
]

const fallbackData = [
  { name: "EC2", value: 12500, color: "oklch(0.7 0.15 200)" },
  { name: "RDS", value: 8200, color: "oklch(0.75 0.12 85)" },
  { name: "S3", value: 4500, color: "oklch(0.65 0.18 145)" },
  { name: "Lambda", value: 2800, color: "oklch(0.7 0.12 280)" },
  { name: "Outros", value: 3200, color: "oklch(0.5 0 0)" },
]

interface ServiceBreakdownProps {
  data?: Array<{ name: string; cost: number }>
}

export function ServiceBreakdown({ data }: ServiceBreakdownProps) {
  const chartData = data && data.length > 0
    ? data.map((item, index) => ({
        name: item.name,
        value: item.cost,
        color: COLORS[index % COLORS.length],
      }))
    : fallbackData

  const total = chartData.reduce((acc, item) => acc + item.value, 0)

  return (
    <div className="p-6 bg-card rounded-xl border border-border">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-card-foreground">
          Custos por Servico
        </h3>
        <p className="text-sm text-muted-foreground">Distribuicao mensal</p>
      </div>

      <div className="flex items-center gap-6">
        <div className="w-[180px] h-[180px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={80}
                paddingAngle={2}
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: "oklch(0.17 0.005 285)",
                  border: "1px solid oklch(0.28 0.005 285)",
                  borderRadius: "8px",
                  color: "oklch(0.95 0 0)",
                }}
                formatter={(value: number) => [`$${value.toLocaleString()}`, ""]}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="flex-1 space-y-3">
          {chartData.map((item) => (
            <div key={item.name} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-sm text-card-foreground">{item.name}</span>
              </div>
              <div className="text-right">
                <span className="text-sm font-medium text-card-foreground">
                  ${item.value.toLocaleString()}
                </span>
                {total > 0 && (
                  <span className="text-xs text-muted-foreground ml-2">
                    {((item.value / total) * 100).toFixed(0)}%
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
