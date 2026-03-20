"use client";

import { BusinessMetrics } from "@/lib/supabase";

type BusinessMetricsPanelProps = {
  metrics: BusinessMetrics | null;
  clientMode: boolean;
};

export default function BusinessMetricsPanel({ metrics, clientMode }: BusinessMetricsPanelProps) {
  const stats = [
    { label: "Leads Today", value: metrics?.leads_today || 0, color: "text-blue-400" },
    { label: "Conversion Rate", value: `${metrics?.conversion_rate || 0}%`, color: "text-emerald-400" },
    { label: "Revenue Total", value: clientMode ? "HIDDEN" : `$${(metrics?.revenue_total || 0).toLocaleString()}`, color: "text-green-400" },
    { label: "Pipeline Value", value: clientMode ? "HIDDEN" : `$${(metrics?.pipeline_value || 0).toLocaleString()}`, color: "text-purple-400" },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat) => (
        <div key={stat.label} className="p-4 rounded-xl border border-[var(--border)] bg-[var(--bg-card)]">
          <p className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">{stat.label}</p>
          <p className={`text-2xl font-bold mt-2 ${stat.color}`}>{stat.value}</p>
        </div>
      ))}
    </div>
  );
}
