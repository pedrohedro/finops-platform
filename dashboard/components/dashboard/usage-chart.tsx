"use client"

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

const fallbackData = [
  { name: "us-east-1", cost: 15200 },
  { name: "us-west-2", cost: 8400 },
  { name: "eu-west-1", cost: 4200 },
  { name: "ap-south-1", cost: 2800 },
  { name: "sa-east-1", cost: 1600 },
]

interface UsageChartProps {
  data?: Array<{ name: string; cost: number }>
}

export function UsageChart({ data }: UsageChartProps) {
  const chartData = data && data.length > 0 ? data : fallbackData

  return (
    <div className="p-6 bg-card rounded-xl border border-border">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-card-foreground">
          Custos por Ambiente
        </h3>
        <p className="text-sm text-muted-foreground">Distribuicao por environment</p>
      </div>

      <div className="h-[250px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.28 0.005 285)" horizontal={false} />
            <XAxis
              type="number"
              stroke="oklch(0.65 0 0)"
              tick={{ fill: "oklch(0.65 0 0)", fontSize: 12 }}
              axisLine={{ stroke: "oklch(0.28 0.005 285)" }}
              tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
            />
            <YAxis
              type="category"
              dataKey="name"
              stroke="oklch(0.65 0 0)"
              tick={{ fill: "oklch(0.65 0 0)", fontSize: 12 }}
              axisLine={{ stroke: "oklch(0.28 0.005 285)" }}
              width={100}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "oklch(0.17 0.005 285)",
                border: "1px solid oklch(0.28 0.005 285)",
                borderRadius: "8px",
                color: "oklch(0.95 0 0)",
              }}
              formatter={(value: number) => [`$${value.toLocaleString()}`, "Custo"]}
            />
            <Bar
              dataKey="cost"
              fill="oklch(0.7 0.15 200)"
              radius={[0, 4, 4, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
