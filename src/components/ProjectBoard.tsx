"use client";

import { useState } from "react";

type PipelineItem = {
  id: string;
  title: string;
  description: string;
  status: "done" | "in_progress" | "blocked" | "pending";
  owner: string;
  priority: "critical" | "high" | "medium" | "low";
  blockedBy?: string;
};

const pipeline: PipelineItem[] = [
  {
    id: "1",
    title: "Agency Foundation",
    description: "SOUL, IDENTITY, USER, TOOLS, EXECUTION-PLAN, team of 20 agents defined",
    status: "done",
    owner: "Max",
    priority: "critical",
  },
  {
    id: "2",
    title: "Campaign Kit — Website Rebuilds",
    description: "Landing page copy, 5 Meta ads, sales script, outreach messages, email nurture sequence, funnel flow",
    status: "done",
    owner: "Copy / Blaze",
    priority: "critical",
  },
  {
    id: "3",
    title: "AI Search Visibility Audit",
    description: "Full SEO/AI audit of digitaloneagency.com.au. Rank Math fixes applied. llms.txt created.",
    status: "done",
    owner: "Rank",
    priority: "high",
  },
  {
    id: "4",
    title: "Dashboard & Control System",
    description: "Next.js Business Control System — agent monitoring, metrics, real-time sync",
    status: "done",
    owner: "Nova / Atlas",
    priority: "high",
  },
  {
    id: "5",
    title: "Infrastructure Connected",
    description: "GitHub, Supabase, Vercel, API keys (OpenAI, Anthropic, DeepSeek, Gemini, Figma, Unsplash)",
    status: "done",
    owner: "Pulse",
    priority: "critical",
  },
  {
    id: "6",
    title: "Landing Page Live",
    description: "Deploy website rebuild landing page — Elementor build or standalone HTML on Vercel",
    status: "blocked",
    owner: "Nova / Aura",
    priority: "critical",
    blockedBy: "WP REST API can't match Elementor. Needs manual Elementor build or Vercel deploy.",
  },
  {
    id: "7",
    title: "CRM Schema in Supabase",
    description: "Build leads, clients, projects, invoices tables. Wire form submissions.",
    status: "pending",
    owner: "Forge / Atlas",
    priority: "critical",
  },
  {
    id: "8",
    title: "Lead Automation Pipeline",
    description: "Form → CRM → instant SMS/email response → nurture sequence",
    status: "pending",
    owner: "Logic / Synapse",
    priority: "high",
  },
  {
    id: "9",
    title: "Meta Ads Launch",
    description: "Deploy 5 ad creatives. $50-150/day initial. Requires live landing page + Business Manager access.",
    status: "blocked",
    owner: "Blaze",
    priority: "critical",
    blockedBy: "Needs landing page live + Meta Business Manager details",
  },
  {
    id: "10",
    title: "Google Ads Setup",
    description: "Create account, build search campaigns for website rebuild + AI systems keywords",
    status: "pending",
    owner: "Blaze",
    priority: "medium",
  },
  {
    id: "11",
    title: "Outbound Pipeline",
    description: "Cold outreach to finance brokers, bad-website businesses, app idea founders",
    status: "pending",
    owner: "Hunter / Social",
    priority: "high",
  },
  {
    id: "12",
    title: "Ken's Manual Fixes",
    description: "Purge SG cache, upload llms.txt, reduce H1 tags to 1, create /fintech/ page",
    status: "blocked",
    owner: "Ken",
    priority: "medium",
    blockedBy: "Requires WordPress admin access / SiteGround panel",
  },
  {
    id: "13",
    title: "NDIS Marketplace",
    description: "Early concept/preview. Needs full scoping and client confirmation.",
    status: "pending",
    owner: "Atlas / Aura",
    priority: "low",
  },
];

const statusConfig = {
  done: { label: "DONE", color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30", dot: "bg-emerald-400", barColor: "bg-emerald-500" },
  in_progress: { label: "ACTIVE", color: "bg-blue-500/20 text-blue-400 border-blue-500/30", dot: "bg-blue-400 animate-pulse", barColor: "bg-blue-500" },
  blocked: { label: "BLOCKED", color: "bg-red-500/20 text-red-400 border-red-500/30", dot: "bg-red-400", barColor: "bg-red-500" },
  pending: { label: "QUEUED", color: "bg-gray-500/20 text-gray-400 border-gray-500/30", dot: "bg-gray-400", barColor: "bg-gray-600" },
};

const priorityConfig = {
  critical: "text-red-400",
  high: "text-orange-400",
  medium: "text-yellow-400",
  low: "text-gray-400",
};

type FilterTab = "all" | "done" | "blocked" | "pending";

export default function ProjectBoard() {
  const [filter, setFilter] = useState<FilterTab>("all");

  const filtered = filter === "all" ? pipeline : pipeline.filter(i => i.status === filter);
  const doneCount = pipeline.filter(i => i.status === "done").length;
  const blockedCount = pipeline.filter(i => i.status === "blocked").length;
  const pendingCount = pipeline.filter(i => i.status === "pending").length;
  const progress = Math.round((doneCount / pipeline.length) * 100);

  const tabs: { key: FilterTab; label: string; count: number }[] = [
    { key: "all", label: "ALL", count: pipeline.length },
    { key: "done", label: "DONE", count: doneCount },
    { key: "blocked", label: "BLOCKED", count: blockedCount },
    { key: "pending", label: "QUEUED", count: pendingCount },
  ];

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] overflow-hidden">
      <div className="p-4 border-b border-[var(--border)] bg-[var(--bg-secondary)]/30">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-bold text-[var(--text-primary)] font-mono flex items-center gap-2">
            <span className="text-blue-500">🚀</span> EXECUTION_PIPELINE
          </h2>
          <span className="text-[10px] font-mono text-emerald-400 font-bold">{progress}% COMPLETE</span>
        </div>
        {/* Progress bar */}
        <div className="w-full h-2 bg-[var(--bg-primary)] rounded-full overflow-hidden border border-[var(--border)]">
          <div
            className="h-full bg-gradient-to-r from-emerald-500 to-blue-500 transition-all duration-1000 rounded-full"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex items-center justify-between mt-2 text-[9px] font-mono text-[var(--text-secondary)]">
          <span>{doneCount} completed</span>
          <span>{blockedCount} blocked</span>
          <span>{pendingCount} queued</span>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 p-2 border-b border-[var(--border)] bg-[var(--bg-secondary)]/20">
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            className={`text-[9px] px-3 py-1 rounded font-bold font-mono transition-all ${
              filter === tab.key
                ? "bg-blue-500/20 border border-blue-500/40 text-blue-400"
                : "border border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            }`}
          >
            {tab.label} ({tab.count})
          </button>
        ))}
      </div>

      <div className="divide-y divide-[var(--border)] max-h-[500px] overflow-y-auto">
        {filtered.map((item) => {
          const sc = statusConfig[item.status];
          return (
            <div key={item.id} className="p-3 hover:bg-[var(--bg-card-hover)] transition-colors group">
              <div className="flex items-start gap-3">
                <div className={`w-1 self-stretch rounded-full ${sc.barColor} shrink-0 mt-1`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <div className="flex items-center gap-2 min-w-0">
                      <h3 className="text-xs font-bold text-[var(--text-primary)] truncate">{item.title}</h3>
                      <span className={`text-[8px] font-bold ${priorityConfig[item.priority]}`}>
                        {item.priority.toUpperCase()}
                      </span>
                    </div>
                    <span className={`shrink-0 inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[8px] font-bold border ${sc.color}`}>
                      <span className={`w-1 h-1 rounded-full ${sc.dot}`} />
                      {sc.label}
                    </span>
                  </div>
                  <p className="text-[10px] text-[var(--text-secondary)] leading-relaxed">{item.description}</p>
                  <div className="flex items-center gap-3 mt-1.5">
                    <span className="text-[9px] font-mono text-blue-400/70">→ {item.owner}</span>
                    {item.blockedBy && (
                      <span className="text-[9px] font-mono text-red-400/70">⚠ {item.blockedBy}</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="p-3 border-t border-[var(--border)] bg-[var(--bg-secondary)]/10 text-[9px] font-mono text-[var(--text-secondary)] flex justify-between">
        <span>LAST_SYNC: {new Date().toLocaleDateString("en-AU")} — DAY 3</span>
        <span className="text-blue-400">MANAGED_BY: MAX</span>
      </div>
    </div>
  );
}
