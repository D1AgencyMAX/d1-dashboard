"use client";

import { Agent } from "@/lib/supabase";

export default function CostBreakdown({ agents }: { agents: Agent[] }) {
  // Group costs by provider
  const providerCosts: Record<string, { cost: number; agents: number; tokens: number }> = {};
  agents.forEach((agent) => {
    const provider = agent.model?.split("/")[0] || "unknown";
    if (!providerCosts[provider]) providerCosts[provider] = { cost: 0, agents: 0, tokens: 0 };
    providerCosts[provider].cost += Number(agent.cost_usd || 0);
    providerCosts[provider].agents += 1;
    providerCosts[provider].tokens += Number(agent.tokens_used || 0);
  });

  const providerColors: Record<string, string> = {
    anthropic: "bg-orange-500",
    openai: "bg-green-500",
    google: "bg-blue-500",
  };

  const providerLabels: Record<string, string> = {
    anthropic: "Anthropic (Claude)",
    openai: "OpenAI (GPT)",
    google: "Google (Gemini)",
  };

  const totalCost = Object.values(providerCosts).reduce((sum, p) => sum + p.cost, 0);

  // Group by department
  const deptCosts: Record<string, { cost: number; tokens: number }> = {};
  agents.forEach((agent) => {
    if (!deptCosts[agent.department]) deptCosts[agent.department] = { cost: 0, tokens: 0 };
    deptCosts[agent.department].cost += Number(agent.cost_usd || 0);
    deptCosts[agent.department].tokens += Number(agent.tokens_used || 0);
  });

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] overflow-hidden">
      <div className="p-4 border-b border-[var(--border)]">
        <h2 className="text-lg font-semibold text-[var(--text-primary)]">💰 Cost Breakdown</h2>
      </div>

      <div className="p-4 space-y-4">
        {/* Provider breakdown */}
        <div>
          <h3 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-3">By Provider</h3>
          <div className="space-y-3">
            {Object.entries(providerCosts)
              .sort((a, b) => b[1].cost - a[1].cost)
              .map(([provider, data]) => (
                <div key={provider}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-[var(--text-primary)]">
                      {providerLabels[provider] || provider}
                    </span>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-[var(--text-secondary)]">{data.agents} agents</span>
                      <span className="text-sm font-semibold text-[var(--text-primary)]">${data.cost.toFixed(2)}</span>
                    </div>
                  </div>
                  <div className="w-full h-2 bg-[var(--bg-primary)] rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${providerColors[provider] || "bg-gray-500"} transition-all duration-500`}
                      style={{ width: totalCost > 0 ? `${(data.cost / totalCost) * 100}%` : "0%" }}
                    />
                  </div>
                </div>
              ))}
          </div>
        </div>

        {/* Department breakdown */}
        <div className="pt-4 border-t border-[var(--border)]">
          <h3 className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-3">By Department</h3>
          <div className="space-y-2">
            {Object.entries(deptCosts)
              .sort((a, b) => b[1].cost - a[1].cost)
              .map(([dept, data]) => (
                <div key={dept} className="flex items-center justify-between py-1">
                  <span className="text-sm text-[var(--text-primary)]">{dept}</span>
                  <div className="flex items-center gap-4">
                    <span className="text-xs text-[var(--text-secondary)] font-mono">
                      {data.tokens > 1000 ? `${(data.tokens / 1000).toFixed(0)}K` : data.tokens} tok
                    </span>
                    <span className="text-sm font-semibold text-[var(--text-primary)] w-16 text-right">${data.cost.toFixed(2)}</span>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}
