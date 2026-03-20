"use client";

import { Agent } from "@/lib/supabase";
import StatusBadge from "./StatusBadge";

const departmentColors: Record<string, string> = {
  Leadership: "border-l-yellow-500",
  Engineering: "border-l-blue-500",
  Design: "border-l-pink-500",
  Marketing: "border-l-green-500",
  "AI & Automation": "border-l-purple-500",
  "Data & Finance": "border-l-cyan-500",
  Sales: "border-l-orange-500",
  "R&D": "border-l-indigo-500",
  Trading: "border-l-red-500",
};

const departmentEmoji: Record<string, string> = {
  Leadership: "👑",
  Engineering: "🔧",
  Design: "🎨",
  Marketing: "📈",
  "AI & Automation": "🤖",
  "Data & Finance": "📊",
  Sales: "🎯",
  "R&D": "🔬",
  Trading: "📉",
};

export default function AgentGrid({ agents, clientMode }: { agents: Agent[], clientMode: boolean }) {
  // Group by department
  const departments = agents.reduce((acc, agent) => {
    if (!acc[agent.department]) acc[agent.department] = [];
    acc[agent.department].push(agent);
    return acc;
  }, {} as Record<string, Agent[]>);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-[var(--text-primary)]">🤖 Agent Fleet</h2>
        <div className="flex gap-3 text-xs text-[var(--text-secondary)]">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" /> Working
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-gray-400" /> Idle
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-red-400" /> Error
          </span>
        </div>
      </div>

      {Object.entries(departments).map(([dept, deptAgents]) => (
        <div key={dept}>
          <div className="flex items-center gap-2 mb-3">
            <span>{departmentEmoji[dept] || "📁"}</span>
            <h3 className="text-sm font-medium text-[var(--text-secondary)] uppercase tracking-wider">{dept}</h3>
            <span className="text-xs text-[var(--text-secondary)] bg-[var(--bg-card)] px-2 py-0.5 rounded-full">
              {deptAgents.filter((a) => a.status === "working").length}/{deptAgents.length}
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {deptAgents.map((agent) => (
              <div
                key={agent.id}
                className={`relative rounded-lg border-l-4 ${departmentColors[dept] || "border-l-gray-500"} bg-[var(--bg-card)] border border-[var(--border)] p-4 transition-all hover:bg-[var(--bg-card-hover)] hover:border-[var(--accent-blue)]/30 ${agent.status === "working" ? "shadow-[0_0_15px_rgba(59,130,246,0.1)] border-blue-500/30" : ""}`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h4 className="font-semibold text-sm text-[var(--text-primary)]">{agent.name}</h4>
                    <p className="text-xs text-[var(--text-secondary)]">{agent.role}</p>
                  </div>
                  <StatusBadge status={agent.status} />
                </div>

                {agent.current_task && (
                  <div className="mb-3 p-2 rounded-md bg-blue-500/10 border border-blue-500/20">
                    <p className="text-xs text-blue-300 font-medium">Currently:</p>
                    <p className="text-xs text-blue-200 mt-0.5 truncate">{agent.current_task}</p>
                  </div>
                )}

                <div className="grid grid-cols-3 gap-2 text-center">
                  <div>
                    <p className="text-xs text-[var(--text-secondary)]">Tasks</p>
                    <p className="text-sm font-semibold text-[var(--text-primary)]">{agent.tasks_completed}</p>
                  </div>
                  <div>
                    <p className="text-xs text-[var(--text-secondary)]">Tokens</p>
                    <p className="text-sm font-semibold text-[var(--text-primary)]">
                      {agent.tokens_used > 1000 ? `${(agent.tokens_used / 1000).toFixed(0)}K` : agent.tokens_used}
                    </p>
                  </div>
                  {!clientMode && (
                    <div>
                      <p className="text-xs text-[var(--text-secondary)]">Cost</p>
                      <p className="text-sm font-semibold text-[var(--text-primary)]">${Number(agent.cost_usd || 0).toFixed(2)}</p>
                    </div>
                  )}
                </div>

                <div className="mt-2 pt-2 border-t border-[var(--border)]">
                  <p className="text-[10px] text-[var(--text-secondary)] font-mono truncate">{clientMode ? "MANAGED AGENT" : agent.model}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
