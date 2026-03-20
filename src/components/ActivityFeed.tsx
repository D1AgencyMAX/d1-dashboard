"use client";

import { ActivityItem } from "@/lib/supabase";

const eventIcons: Record<string, string> = {
  task_started: "🚀",
  task_completed: "✅",
  task_failed: "❌",
  agent_online: "🟢",
  agent_offline: "🔴",
  project_created: "📁",
  project_completed: "🏆",
  cost_alert: "⚠️",
  system: "⚙️",
  deployment: "🚢",
};

function timeAgo(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

export default function ActivityFeed({ activities }: { activities: ActivityItem[] }) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] overflow-hidden">
      <div className="p-4 border-b border-[var(--border)]">
        <h2 className="text-lg font-semibold text-[var(--text-primary)]">📡 Live Activity</h2>
      </div>
      <div className="divide-y divide-[var(--border)] max-h-[400px] overflow-y-auto">
        {activities.length === 0 ? (
          <div className="p-8 text-center text-[var(--text-secondary)]">
            <p className="text-3xl mb-2">🔇</p>
            <p className="text-sm">No activity yet — agents are standing by</p>
          </div>
        ) : (
          activities.map((item) => (
            <div key={item.id} className="p-3 hover:bg-[var(--bg-card-hover)] transition-colors">
              <div className="flex items-start gap-3">
                <span className="text-lg mt-0.5">{eventIcons[item.event_type] || "📌"}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[var(--text-primary)]">{item.title}</p>
                  {item.description && (
                    <p className="text-xs text-[var(--text-secondary)] mt-0.5 truncate">{item.description}</p>
                  )}
                </div>
                <span className="text-xs text-[var(--text-secondary)] whitespace-nowrap">{timeAgo(item.created_at)}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
