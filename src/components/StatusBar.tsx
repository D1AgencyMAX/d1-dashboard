"use client";

import { Agent, SystemMetrics } from "@/lib/supabase";

type StatusBarProps = {
  metrics: SystemMetrics | null;
  agents: Agent[];
  clientMode: boolean;
};

export default function StatusBar({ metrics, agents, clientMode }: StatusBarProps) {
  const activeAgents = agents.filter(a => a.status === 'working').length;
  const totalCost = agents.reduce((sum, a) => sum + Number(a.cost_usd || 0), 0);

  return (
    <div className="flex items-center gap-6 text-xs font-medium px-4 py-2 bg-[var(--bg-secondary)] border-b border-[var(--border)]">
      <div className="flex items-center gap-2">
        <span className="text-[var(--text-secondary)]">SYSTEM STATUS:</span>
        <span className={`px-1.5 py-0.5 rounded ${metrics?.gateway_status === 'OK' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
          {metrics?.gateway_status || 'OK'}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-[var(--text-secondary)]">ACTIVE AGENTS:</span>
        <span className="text-[var(--text-primary)]">{activeAgents} / {agents.length}</span>
      </div>
      {!clientMode && (
        <div className="flex items-center gap-2">
          <span className="text-[var(--text-secondary)]">DAILY COST:</span>
          <span className="text-[var(--accent-blue)]">${totalCost.toFixed(2)}</span>
        </div>
      )}
      <div className="flex items-center gap-2">
        <span className="text-[var(--text-secondary)]">API ERRORS:</span>
        <span className="text-green-400">0</span>
      </div>
      <div className="flex-1" />
      <div className="flex items-center gap-2 text-[var(--text-secondary)]">
        <span>MODE:</span>
        <span className={`px-1.5 py-0.5 rounded ${clientMode ? 'bg-blue-500/10 text-blue-400' : 'bg-purple-500/10 text-purple-400'}`}>
          {clientMode ? 'CLIENT VIEW' : 'FULL OPS'}
        </span>
      </div>
    </div>
  );
}
