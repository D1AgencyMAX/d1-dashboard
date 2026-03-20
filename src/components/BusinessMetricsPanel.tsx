"use client";

import { BusinessMetrics } from "@/lib/supabase";

type BusinessMetricsPanelProps = {
  metrics: BusinessMetrics | null;
  clientMode: boolean;
};

export default function BusinessMetricsPanel({ metrics, clientMode }: BusinessMetricsPanelProps) {
  const stats = [
    {
      label: "Pipeline Stage",
      value: "PRE-LAUNCH",
      sub: "Landing page → Ads → First client",
      color: "text-amber-400",
      icon: "🎯",
    },
    {
      label: "Leads Today",
      value: metrics?.leads_today || 0,
      sub: "Awaiting ad launch",
      color: "text-blue-400",
      icon: "📥",
    },
    {
      label: "Revenue",
      value: clientMode ? "HIDDEN" : `$${(metrics?.revenue_total || 0).toLocaleString()}`,
      sub: clientMode ? "" : "Target: $50K/mo",
      color: "text-green-400",
      icon: "💵",
    },
    {
      label: "Pipeline Value",
      value: clientMode ? "HIDDEN" : `$${(metrics?.pipeline_value || 0).toLocaleString()}`,
      sub: clientMode ? "" : "Active opportunities",
      color: "text-purple-400",
      icon: "📊",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat) => (
        <div key={stat.label} className="relative overflow-hidden p-4 rounded-xl border border-[var(--border)] bg-[var(--bg-card)] group hover:border-[var(--accent-blue)]/30 transition-all">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-[10px] font-medium text-[var(--text-secondary)] uppercase tracking-wider font-mono">{stat.label}</p>
              <p className={`text-2xl font-bold mt-1.5 ${stat.color}`}>{stat.value}</p>
              {stat.sub && <p className="text-[10px] text-[var(--text-secondary)] mt-1 font-mono">{stat.sub}</p>}
            </div>
            <span className="text-xl opacity-50 group-hover:opacity-100 transition-opacity">{stat.icon}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
