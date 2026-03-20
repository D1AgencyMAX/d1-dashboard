"use client";

import { Agent, Task } from "@/lib/supabase";

type StatsCardsProps = {
  agents: Agent[];
  tasks: Task[];
};

export default function StatsCards({ agents, tasks }: StatsCardsProps) {
  const activeAgents = agents.filter((a) => a.status === "working").length;
  const totalCost = agents.reduce((sum, a) => sum + Number(a.cost_usd || 0), 0);
  const totalTokens = agents.reduce((sum, a) => sum + Number(a.tokens_used || 0), 0);
  const totalTasksCompleted = agents.reduce((sum, a) => sum + (a.tasks_completed || 0), 0);
  const activeTasks = tasks.filter((t) => t.status === "in_progress").length;
  const pendingTasks = tasks.filter((t) => t.status === "pending").length;

  const stats = [
    {
      label: "Active Agents",
      value: `${activeAgents}/${agents.length}`,
      icon: "⚡",
      color: "from-blue-500/20 to-blue-600/5 border-blue-500/20",
      accent: "text-blue-400",
    },
    {
      label: "Tasks Running",
      value: activeTasks.toString(),
      sub: `${pendingTasks} pending`,
      icon: "🔄",
      color: "from-green-500/20 to-green-600/5 border-green-500/20",
      accent: "text-green-400",
    },
    {
      label: "Tasks Completed",
      value: totalTasksCompleted.toLocaleString(),
      icon: "✅",
      color: "from-emerald-500/20 to-emerald-600/5 border-emerald-500/20",
      accent: "text-emerald-400",
    },
    {
      label: "Total Tokens",
      value: totalTokens > 1_000_000 ? `${(totalTokens / 1_000_000).toFixed(1)}M` : totalTokens > 1000 ? `${(totalTokens / 1000).toFixed(1)}K` : totalTokens.toString(),
      icon: "🧮",
      color: "from-purple-500/20 to-purple-600/5 border-purple-500/20",
      accent: "text-purple-400",
    },
    {
      label: "Total Cost",
      value: `$${totalCost.toFixed(2)}`,
      icon: "💰",
      color: "from-yellow-500/20 to-yellow-600/5 border-yellow-500/20",
      accent: "text-yellow-400",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className={`relative overflow-hidden rounded-xl border bg-gradient-to-br ${stat.color} p-4 transition-all hover:scale-[1.02]`}
        >
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">{stat.label}</p>
              <p className={`text-2xl font-bold mt-1 ${stat.accent}`}>{stat.value}</p>
              {stat.sub && <p className="text-xs text-[var(--text-secondary)] mt-0.5">{stat.sub}</p>}
            </div>
            <span className="text-2xl">{stat.icon}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
