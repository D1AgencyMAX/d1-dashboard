"use client";

import { useMemo } from "react";
import {
  AdChannel,
  CapacityItem,
  DashboardAlert,
  Deal,
  FunnelStage,
  MarginItem,
  QuickAction,
  RevenueSeriesPoint,
  RevenueTarget,
  compactCurrency,
  currency,
  formatCloseDate,
  percent,
} from "@/lib/dashboard";

type HeaderProps = {
  connected: boolean;
  updatedAt: Date;
};

export function DashboardHeader({ connected, updatedAt }: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 border-b border-white/10 bg-slate-950/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.28em] text-cyan-300/80">Digital One Agency</p>
          <h1 className="mt-1 text-2xl font-semibold text-white sm:text-3xl">Revenue command dashboard</h1>
        </div>
        <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-300">
          <span className={`h-2.5 w-2.5 rounded-full ${connected ? "bg-emerald-400" : "bg-amber-400"}`} />
          <div>
            <p className="font-medium text-white">{connected ? "Realtime connected" : "Realtime reconnecting"}</p>
            <p className="text-xs text-slate-400">Updated {updatedAt.toLocaleTimeString("en-AU", { hour: "2-digit", minute: "2-digit" })}</p>
          </div>
        </div>
      </div>
    </header>
  );
}

type HeroProps = {
  weeklyRevenue: number;
  weeklyTarget: number;
  leadsThisWeek: number;
  closeRate: number;
  pipelineValue: number;
  weightedPipeline: number;
  avgDealSize: number;
};

export function HeroMetrics(props: HeroProps) {
  const pace = props.weeklyTarget === 0 ? 0 : (props.weeklyRevenue / props.weeklyTarget) * 100;
  const metrics = [
    { label: "This week", value: currency(props.weeklyRevenue), sub: `${percent(pace)} of ${currency(props.weeklyTarget)} target` },
    { label: "Leads this week", value: String(props.leadsThisWeek), sub: "Inbound + outbound combined" },
    { label: "Close rate", value: percent(props.closeRate), sub: "Qualified to won" },
    { label: "Weighted pipeline", value: currency(props.weightedPipeline), sub: `${currency(props.pipelineValue)} gross pipeline` },
    { label: "Average deal size", value: currency(props.avgDealSize), sub: "$60K build benchmark" },
  ];

  return (
    <section className="grid gap-4 lg:grid-cols-[1.4fr_repeat(4,1fr)]">
      <div className="rounded-3xl border border-cyan-400/20 bg-gradient-to-br from-cyan-400/12 via-slate-900 to-slate-950 p-6 shadow-2xl shadow-cyan-500/10 lg:col-span-1">
        <p className="text-sm font-medium text-cyan-200">Primary focus</p>
        <h2 className="mt-2 max-w-sm text-3xl font-semibold leading-tight text-white">Track revenue pace, unblock deals, and fix ad efficiency fast.</h2>
        <div className="mt-6 h-2 w-full overflow-hidden rounded-full bg-white/10">
          <div className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-emerald-400" style={{ width: `${Math.min(pace, 100)}%` }} />
        </div>
        <div className="mt-3 flex items-center justify-between text-sm text-slate-300">
          <span>Weekly target pace</span>
          <span className="font-semibold text-white">{percent(pace)}</span>
        </div>
      </div>
      {metrics.slice(1).map((metric) => (
        <div key={metric.label} className="rounded-3xl border border-white/10 bg-white/5 p-5">
          <p className="text-sm text-slate-400">{metric.label}</p>
          <p className="mt-3 text-3xl font-semibold text-white">{metric.value}</p>
          <p className="mt-2 text-sm text-slate-400">{metric.sub}</p>
        </div>
      ))}
    </section>
  );
}

export function RevenueTargetsCard({ items }: { items: RevenueTarget[] }) {
  return (
    <section className="rounded-3xl border border-white/10 bg-white/5 p-6">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Revenue vs target</h3>
          <p className="text-sm text-slate-400">Daily, weekly, and monthly performance against goal.</p>
        </div>
      </div>
      <div className="space-y-5">
        {items.map((item) => {
          const progress = item.target === 0 ? 0 : Math.min((item.actual / item.target) * 100, 100);
          const healthy = item.actual >= item.target * 0.9;
          return (
            <div key={item.period}>
              <div className="mb-2 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium capitalize text-white">{item.period}</p>
                  <p className="text-xs text-slate-400">{currency(item.actual)} actual / {currency(item.target)} target</p>
                </div>
                <span className={`text-sm font-semibold ${healthy ? "text-emerald-300" : "text-amber-300"}`}>{percent(progress)}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-white/10">
                <div className={`h-full rounded-full ${healthy ? "bg-emerald-400" : "bg-amber-400"}`} style={{ width: `${progress}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export function RevenueChart({ points }: { points: RevenueSeriesPoint[] }) {
  const maxValue = useMemo(() => Math.max(...points.map((p) => Math.max(p.revenue, p.target))), [points]);

  return (
    <section className="rounded-3xl border border-white/10 bg-white/5 p-6">
      <div className="mb-5">
        <h3 className="text-lg font-semibold text-white">Revenue pace this week</h3>
        <p className="text-sm text-slate-400">Actual revenue against the required daily run rate.</p>
      </div>
      <div className="flex h-64 items-end gap-3">
        {points.map((point) => {
          const revenueHeight = maxValue ? (point.revenue / maxValue) * 100 : 0;
          const targetHeight = maxValue ? (point.target / maxValue) * 100 : 0;
          const ahead = point.revenue >= point.target;
          return (
            <div key={point.label} className="flex flex-1 flex-col items-center gap-3">
              <div className="relative flex h-full w-full items-end justify-center gap-2 rounded-2xl bg-slate-950/60 px-2 py-3">
                <div className="w-3 rounded-full bg-white/15" style={{ height: `${targetHeight}%` }} />
                <div className={`w-5 rounded-full ${ahead ? "bg-emerald-400" : "bg-cyan-400"}`} style={{ height: `${revenueHeight}%` }} />
              </div>
              <div className="text-center">
                <p className="text-sm font-medium text-white">{point.label}</p>
                <p className="text-xs text-slate-400">{currency(point.revenue)}</p>
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-4 flex items-center gap-4 text-xs text-slate-400">
        <span className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-cyan-400" /> Actual</span>
        <span className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-white/30" /> Target</span>
      </div>
    </section>
  );
}

export function PipelineCard({ stages }: { stages: FunnelStage[] }) {
  const maxCount = Math.max(...stages.map((stage) => stage.count));
  return (
    <section className="rounded-3xl border border-white/10 bg-white/5 p-6">
      <div className="mb-5">
        <h3 className="text-lg font-semibold text-white">Lead pipeline</h3>
        <p className="text-sm text-slate-400">From source to closed deal, focused on movement not vanity.</p>
      </div>
      <div className="space-y-4">
        {stages.map((stage) => (
          <div key={stage.id} className="rounded-2xl border border-white/8 bg-slate-950/50 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-white">{stage.label}</p>
                <p className="text-xs text-slate-400">{compactCurrency(stage.value)} value</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-semibold text-white">{stage.count}</p>
                {typeof stage.conversionFromPrev === "number" && <p className="text-xs text-emerald-300">{percent(stage.conversionFromPrev, 1)} from previous</p>}
              </div>
            </div>
            <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
              <div className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-blue-500" style={{ width: `${(stage.count / maxCount) * 100}%` }} />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

export function DealsTable({ deals }: { deals: Deal[] }) {
  const healthStyles: Record<Deal["health"], string> = {
    strong: "text-emerald-300 bg-emerald-400/10",
    watch: "text-amber-300 bg-amber-400/10",
    risk: "text-rose-300 bg-rose-400/10",
  };

  return (
    <section className="rounded-3xl border border-white/10 bg-white/5 p-6">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Active deals</h3>
          <p className="text-sm text-slate-400">Highest-value opportunities likely to move revenue this month.</p>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="text-slate-400">
            <tr className="border-b border-white/10">
              <th className="pb-3 font-medium">Company</th>
              <th className="pb-3 font-medium">Stage</th>
              <th className="pb-3 font-medium">Owner</th>
              <th className="pb-3 font-medium">Value</th>
              <th className="pb-3 font-medium">Probability</th>
              <th className="pb-3 font-medium">Close</th>
              <th className="pb-3 font-medium">Health</th>
            </tr>
          </thead>
          <tbody>
            {deals.map((deal) => (
              <tr key={deal.id} className="border-b border-white/6 text-slate-200 last:border-0">
                <td className="py-4">
                  <div>
                    <p className="font-medium text-white">{deal.company}</p>
                    <p className="text-xs text-slate-400">{deal.source}</p>
                  </div>
                </td>
                <td className="py-4 capitalize">{deal.stage}</td>
                <td className="py-4">{deal.owner}</td>
                <td className="py-4 font-medium text-white">{currency(deal.value)}</td>
                <td className="py-4">{percent(deal.probability)}</td>
                <td className="py-4">{formatCloseDate(deal.closeDate)}</td>
                <td className="py-4"><span className={`rounded-full px-3 py-1 text-xs font-medium capitalize ${healthStyles[deal.health]}`}>{deal.health}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function AdsCard({ channels }: { channels: AdChannel[] }) {
  return (
    <section className="rounded-3xl border border-white/10 bg-white/5 p-6">
      <div className="mb-5">
        <h3 className="text-lg font-semibold text-white">Ad performance</h3>
        <p className="text-sm text-slate-400">Spend, CPL, and ROAS across the channels driving pipeline.</p>
      </div>
      <div className="space-y-4">
        {channels.map((channel) => (
          <div key={channel.id} className="rounded-2xl border border-white/8 bg-slate-950/50 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-white">{channel.platform}</p>
                <p className="text-sm text-slate-400">{channel.leads} leads · {channel.trend === "up" ? "Improving" : channel.trend === "down" ? "Down" : "Stable"}</p>
              </div>
              <span className="text-xl">{channel.trend === "up" ? "↗" : channel.trend === "down" ? "↘" : "→"}</span>
            </div>
            <div className="mt-4 grid grid-cols-3 gap-3 text-sm">
              <MetricMini label="Spend" value={currency(channel.spend)} />
              <MetricMini label="CPL" value={currency(channel.cpl)} />
              <MetricMini label="ROAS" value={`${channel.roas.toFixed(1)}x`} />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function MetricMini({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/8 bg-white/5 p-3">
      <p className="text-xs text-slate-400">{label}</p>
      <p className="mt-2 text-lg font-semibold text-white">{value}</p>
    </div>
  );
}

export function CapacityCard({ items }: { items: CapacityItem[] }) {
  return (
    <section className="rounded-3xl border border-white/10 bg-white/5 p-6">
      <div className="mb-5">
        <h3 className="text-lg font-semibold text-white">Team capacity</h3>
        <p className="text-sm text-slate-400">Who is available, who is busy, and who needs relief.</p>
      </div>
      <div className="space-y-4">
        {items.map((item) => (
          <div key={item.id} className="rounded-2xl border border-white/8 bg-slate-950/50 p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-medium text-white">{item.name}</p>
                <p className="text-sm text-slate-400">{item.role}</p>
              </div>
              <span className={`rounded-full px-3 py-1 text-xs font-medium capitalize ${item.status === "available" ? "bg-emerald-400/10 text-emerald-300" : item.status === "busy" ? "bg-cyan-400/10 text-cyan-300" : "bg-rose-400/10 text-rose-300"}`}>{item.status}</span>
            </div>
            <p className="mt-3 text-sm text-slate-300">{item.focus}</p>
            <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
              <div className={`h-full rounded-full ${item.utilisation >= 85 ? "bg-rose-400" : item.utilisation >= 70 ? "bg-cyan-400" : "bg-emerald-400"}`} style={{ width: `${item.utilisation}%` }} />
            </div>
            <p className="mt-2 text-xs text-slate-400">{item.utilisation}% utilised</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export function MarginsCard({ items }: { items: MarginItem[] }) {
  return (
    <section className="rounded-3xl border border-white/10 bg-white/5 p-6">
      <div className="mb-5">
        <h3 className="text-lg font-semibold text-white">Profit margins</h3>
        <p className="text-sm text-slate-400">Keep high-value work profitable. Flag tight or loss-making delivery fast.</p>
      </div>
      <div className="space-y-4">
        {items.map((item) => (
          <div key={item.id} className="rounded-2xl border border-white/8 bg-slate-950/50 p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-medium text-white">{item.client}</p>
                <p className="text-sm text-slate-400">{item.project}</p>
              </div>
              <span className={`rounded-full px-3 py-1 text-xs font-medium ${item.status === "healthy" ? "bg-emerald-400/10 text-emerald-300" : item.status === "tight" ? "bg-amber-400/10 text-amber-300" : "bg-rose-400/10 text-rose-300"}`}>{percent(item.margin, 1)}</span>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
              <MetricMini label="Revenue" value={currency(item.revenue)} />
              <MetricMini label="Cost" value={currency(item.cost)} />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

export function AlertsCard({ items }: { items: DashboardAlert[] }) {
  return (
    <section className="rounded-3xl border border-white/10 bg-white/5 p-6">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Alerts</h3>
          <p className="text-sm text-slate-400">Urgent issues that need action, not vanity reporting.</p>
        </div>
        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">{items.length} live</span>
      </div>
      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.id} className="rounded-2xl border border-white/8 bg-slate-950/60 p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-medium text-white">{item.title}</p>
                <p className="mt-1 text-sm text-slate-400">{item.detail}</p>
              </div>
              <span className={`rounded-full px-3 py-1 text-xs font-medium uppercase ${item.level === "critical" ? "bg-rose-400/10 text-rose-300" : item.level === "warning" ? "bg-amber-400/10 text-amber-300" : "bg-cyan-400/10 text-cyan-300"}`}>{item.level}</span>
            </div>
            <button className="mt-4 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm font-medium text-white transition hover:bg-white/10">{item.action}</button>
          </div>
        ))}
      </div>
    </section>
  );
}

export function QuickActionsCard({ items }: { items: QuickAction[] }) {
  return (
    <section className="rounded-3xl border border-white/10 bg-white/5 p-6">
      <div className="mb-5">
        <h3 className="text-lg font-semibold text-white">Quick actions</h3>
        <p className="text-sm text-slate-400">Fast entry points for the workflows used every day.</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {items.map((item) => (
          <a key={item.id} href={item.href} className="rounded-2xl border border-white/10 bg-slate-950/60 p-4 transition hover:border-cyan-400/40 hover:bg-slate-900">
            <p className="font-medium text-white">{item.label}</p>
            <p className="mt-1 text-sm text-slate-400">{item.description}</p>
          </a>
        ))}
      </div>
    </section>
  );
}
