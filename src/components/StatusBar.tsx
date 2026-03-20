"use client";

import { Agent, SystemMetrics } from "@/lib/supabase";
import { useEffect, useState } from "react";

type StatusBarProps = {
  metrics: SystemMetrics | null;
  agents: Agent[];
  clientMode: boolean;
};

export default function StatusBar({ metrics, agents, clientMode }: StatusBarProps) {
  const [pulse, setPulse] = useState(false);
  const activeAgents = agents.filter(a => a.status === 'working').length;
  const totalCost = agents.reduce((sum, a) => sum + Number(a.cost_usd || 0), 0);

  useEffect(() => {
    const interval = setInterval(() => setPulse(p => !p), 3000);
    return () => clearInterval(interval);
  }, []);

  const getHeartbeatColor = () => {
    if (!metrics) return "bg-gray-500";
    if (metrics.gateway_status === "OK" && metrics.supabase_status === "OK") return "bg-green-400";
    return "bg-yellow-400";
  };

  // Days since launch (March 19, 2026)
  const launchDate = new Date(2026, 2, 19);
  const now = new Date();
  const dayNumber = Math.floor((now.getTime() - launchDate.getTime()) / 86400000) + 1;

  return (
    <div className="flex items-center gap-6 text-[10px] font-mono px-4 py-1.5 bg-[var(--bg-secondary)] border-b border-[var(--border)] uppercase tracking-tighter">
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${getHeartbeatColor()} ${pulse ? 'animate-pulse' : ''}`} />
        <span className="text-[var(--text-secondary)]">MAX:</span>
        <span className={metrics?.gateway_status === 'OK' ? 'text-green-400' : 'text-yellow-400'}>
          {metrics?.gateway_status === 'OK' ? 'ONLINE' : 'CONNECTING'}
        </span>
      </div>

      <div className="flex items-center gap-2 border-l border-[var(--border)] pl-4">
        <span className="text-[var(--text-secondary)]">DAY:</span>
        <span className="text-blue-400 font-bold">{dayNumber}</span>
      </div>
      
      <div className="flex items-center gap-2 border-l border-[var(--border)] pl-4">
        <span className="text-[var(--text-secondary)]">FLEET:</span>
        <span className="text-[var(--text-primary)]">{activeAgents}/{agents.length}</span>
      </div>

      {!clientMode && (
        <div className="flex items-center gap-2 border-l border-[var(--border)] pl-4">
          <span className="text-[var(--text-secondary)]">BURN:</span>
          <span className="text-[var(--accent-blue)]">${totalCost.toFixed(3)}</span>
        </div>
      )}

      <div className="flex-1" />
      
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-[var(--text-secondary)]">GH:</span>
          <span className={metrics?.github_status === 'OK' ? 'text-green-400' : 'text-red-400'}>{metrics?.github_status === 'OK' ? '●' : '○'}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[var(--text-secondary)]">VCL:</span>
          <span className={metrics?.vercel_status === 'OK' ? 'text-green-400' : 'text-red-400'}>{metrics?.vercel_status === 'OK' ? '●' : '○'}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[var(--text-secondary)]">DB:</span>
          <span className={metrics?.supabase_status === 'OK' ? 'text-green-400' : 'text-red-400'}>{metrics?.supabase_status === 'OK' ? '●' : '○'}</span>
        </div>
        <div className="flex items-center gap-2 border-l border-[var(--border)] pl-4">
          <span className={clientMode ? 'text-blue-400' : 'text-purple-400'}>{clientMode ? '🔒 CLIENT' : '⚡ ADMIN'}</span>
        </div>
      </div>
    </div>
  );
}
