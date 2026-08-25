"use client"

import { useEffect, useState, useCallback } from "react"
import { DashboardSidebar } from "@/components/dashboard/sidebar"
import { DashboardHeader } from "@/components/dashboard/header"
import { StatCard } from "@/components/dashboard/stat-card"
import { CostChart } from "@/components/dashboard/cost-chart"
import { ServiceBreakdown } from "@/components/dashboard/service-breakdown"
import { TopResources } from "@/components/dashboard/top-resources"
import { Recommendations } from "@/components/dashboard/recommendations"
import { Alerts } from "@/components/dashboard/alerts"
import { UsageChart } from "@/components/dashboard/usage-chart"
import {
  DollarSign,
  TrendingUp,
  Server,
  Percent,
} from "lucide-react"

const valueFormatter = (number: number) =>
  `$${Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(number)}`

export default function Dashboard() {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080"

  const [days, setDays] = useState("30")
  const [summary, setSummary] = useState({ total_cost: 0, previous_cost: 0 })
  const [topServices, setTopServices] = useState<Array<{ name: string; cost: number }>>([])
  const [chartData, setChartData] = useState<Array<{ date: string; custo: number; previsao: number | null }>>([])
  const [environments, setEnvironments] = useState<Array<{ name: string; cost: number }>>([])
  const [details, setDetails] = useState<any[]>([])
  const [activeServices, setActiveServices] = useState(0)
  const [forecastTotal, setForecastTotal] = useState(0)

  const fetchData = useCallback(async () => {
    try {
      const [sumRes, srvRes, trendRes, envRes, detRes] = await Promise.all([
        fetch(`${API_URL}/api/summary?days=${days}`),
        fetch(`${API_URL}/api/services?days=${days}`),
        fetch(`${API_URL}/api/daily?days=${days}`),
        fetch(`${API_URL}/api/breakdown?days=${days}`),
        fetch(`${API_URL}/api/details?days=7&limit=20`),
      ])

      const sumData = await sumRes.json()
      setSummary(sumData)

      const srvData = await srvRes.json()
      setTopServices(srvData)
      setActiveServices(srvData.length)

      const trendData = await trendRes.json()
      let calcForecast = 0
      const grouped: Record<string, { date: string; custo: number; previsao: number | null }> = {}

      for (const item of trendData) {
        const dateKey = item.date.substring(5)
        if (!grouped[dateKey]) {
          grouped[dateKey] = { date: dateKey, custo: 0, previsao: null }
        }
        if (item.type === "actual") {
          grouped[dateKey].custo += item.cost
        }
        if (item.type === "forecast") {
          grouped[dateKey].previsao = (grouped[dateKey].previsao || 0) + item.cost
          calcForecast += item.cost
        }
      }

      setChartData(Object.values(grouped).sort((a, b) => a.date.localeCompare(b.date)))
      setForecastTotal(calcForecast)

      const envData = await envRes.json()
      setEnvironments(envData)

      const detData = await detRes.json()
      setDetails(detData)
    } catch (e) {
      console.error("Error fetching data", e)
    }
  }, [API_URL, days])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const costDelta = summary.previous_cost > 0
    ? ((summary.total_cost - summary.previous_cost) / summary.previous_cost) * 100
    : 0

  return (
    <div className="min-h-screen bg-background">
      <DashboardSidebar />

      <div className="lg:pl-64">
        <DashboardHeader
          title="Visao Geral"
          days={days}
          onDaysChange={setDays}
        />

        <main className="p-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatCard
              title="Custo Total (Mes)"
              value={valueFormatter(summary.total_cost)}
              change={Math.round(costDelta)}
              changeLabel="vs. mes anterior"
              icon={DollarSign}
              trend={costDelta > 0 ? "up" : "down"}
            />
            <StatCard
              title="Previsao Mensal"
              value={valueFormatter(forecastTotal > 0 ? forecastTotal : summary.total_cost * 1.15)}
              change={15}
              changeLabel="estimado"
              icon={TrendingUp}
              trend="up"
            />
            <StatCard
              title="Servicos Ativos"
              value={String(activeServices || 0)}
              change={-3}
              changeLabel="vs. mes anterior"
              icon={Server}
              trend="down"
            />
            <StatCard
              title="Taxa de Otimizacao"
              value="72%"
              change={5}
              changeLabel="melhoria"
              icon={Percent}
              trend="down"
            />
          </div>

          {/* Main Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            <div className="lg:col-span-2">
              <CostChart data={chartData} />
            </div>
            <ServiceBreakdown data={topServices} />
          </div>

          {/* Secondary Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <TopResources data={details} />
            <UsageChart data={environments} />
          </div>

          {/* Bottom Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Recommendations />
            <Alerts />
          </div>
        </main>
      </div>
    </div>
  )
}
