"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  DollarSign,
  Server,
  Database,
  Cloud,
  Shield,
  Settings,
  TrendingDown,
  AlertTriangle,
  BarChart3,
} from "lucide-react"

const navigation = [
  { name: "Visão Geral", href: "/", icon: LayoutDashboard },
  { name: "Custos", href: "/custos", icon: DollarSign },
  { name: "EC2", href: "/ec2", icon: Server },
  { name: "RDS", href: "/rds", icon: Database },
  { name: "S3", href: "/s3", icon: Cloud },
  { name: "Lambda", href: "/lambda", icon: BarChart3 },
]

const secondaryNav = [
  { name: "Otimização", href: "/otimizacao", icon: TrendingDown },
  { name: "Alertas", href: "/alertas", icon: AlertTriangle },
  { name: "Reservas", href: "/reservas", icon: Shield },
  { name: "Configurações", href: "/configuracoes", icon: Settings },
]

export function DashboardSidebar() {
  const pathname = usePathname()

  return (
    <aside className="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 bg-sidebar border-r border-sidebar-border">
      <div className="flex items-center gap-2 h-16 px-6 border-b border-sidebar-border">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary">
          <Cloud className="w-5 h-5 text-primary-foreground" />
        </div>
        <span className="font-semibold text-sidebar-foreground">AWS FinOps</span>
      </div>

      <nav className="flex-1 px-3 py-4 overflow-y-auto">
        <div className="space-y-1">
          <p className="px-3 text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
            Principal
          </p>
          {navigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 text-sm rounded-lg transition-colors",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-primary"
                    : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground"
                )}
              >
                <item.icon className="w-5 h-5" />
                {item.name}
              </Link>
            )
          })}
        </div>

        <div className="mt-8 space-y-1">
          <p className="px-3 text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
            Gerenciamento
          </p>
          {secondaryNav.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 text-sm rounded-lg transition-colors",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-primary"
                    : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground"
                )}
              >
                <item.icon className="w-5 h-5" />
                {item.name}
              </Link>
            )
          })}
        </div>
      </nav>

      <div className="p-4 border-t border-sidebar-border">
        <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-sidebar-accent">
          <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
            <span className="text-xs font-medium text-primary">JD</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-sidebar-foreground truncate">João Silva</p>
            <p className="text-xs text-muted-foreground truncate">Admin</p>
          </div>
        </div>
      </div>
    </aside>
  )
}
