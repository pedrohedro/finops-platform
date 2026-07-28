"use client"

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

interface CostChartProps {
  data?: Array<{
    date: string
    custo: number
    previsao: number | null
  }>
}

const fallbackData = [
  { date: "01 Mar", custo: 4500, previsao: 4500 },
  { date: "05 Mar", custo: 4800, previsao: 4600 },
  { date: "10 Mar", custo: 5200, previsao: 4700 },
  { date: "15 Mar", custo: 4900, previsao: 4800 },
  { date: "20 Mar", custo: 5400, previsao: 4900 },
  { date: "25 Mar", custo: 5100, previsao: 5000 },
  { date: "30 Mar", custo: 5800, previsao: 5100 },
]

export function CostChart({ data }: CostChartProps) {
  const chartData = data && data.length > 0 ? data : fallbackData

  return (
    <div className="p-6 bg-card rounded-xl border border-border">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-card-foreground">
            Custos ao Longo do Tempo
          </h3>
          <p className="text-sm text-muted-foreground">
            Custo real vs. previsao
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-chart-1" />
            <span className="text-sm text-muted-foreground">Custo Real</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-chart-2" />
            <span className="text-sm text-muted-foreground">Previsao</span>
          </div>
        </div>
      </div>

      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorCusto" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="oklch(0.7 0.15 200)" stopOpacity={0.3} />
                <stop offset="95%" stopColor="oklch(0.7 0.15 200)" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorPrevisao" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="oklch(0.75 0.12 85)" stopOpacity={0.3} />
                <stop offset="95%" stopColor="oklch(0.75 0.12 85)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.28 0.005 285)" />
            <XAxis
              dataKey="date"
              stroke="oklch(0.65 0 0)"
              tick={{ fill: "oklch(0.65 0 0)", fontSize: 12 }}
              axisLine={{ stroke: "oklch(0.28 0.005 285)" }}
            />
            <YAxis
              stroke="oklch(0.65 0 0)"
              tick={{ fill: "oklch(0.65 0 0)", fontSize: 12 }}
              axisLine={{ stroke: "oklch(0.28 0.005 285)" }}
              tickFormatter={(value) => `$${value}`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "oklch(0.17 0.005 285)",
                border: "1px solid oklch(0.28 0.005 285)",
                borderRadius: "8px",
                color: "oklch(0.95 0 0)",
              }}
              formatter={(value: number) => [`$${value.toLocaleString()}`, ""]}
            />
            <Area
              type="monotone"
              dataKey="previsao"
              stroke="oklch(0.75 0.12 85)"
              fillOpacity={1}
              fill="url(#colorPrevisao)"
              strokeWidth={2}
              connectNulls={false}
            />
            <Area
              type="monotone"
              dataKey="custo"
              stroke="oklch(0.7 0.15 200)"
              fillOpacity={1}
              fill="url(#colorCusto)"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
