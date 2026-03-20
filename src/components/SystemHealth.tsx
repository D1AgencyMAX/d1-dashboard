"use client";

import { SystemMetrics } from "@/lib/supabase";

export default function SystemHealth({ metrics }: { metrics: SystemMetrics | null }) {
  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${mins}m`;
  };

  const StatusLight = ({ status }: { status: string | null }) => (
    <div className={`w-2 h-2 rounded-full ${status === "OK" ? "bg-green-400" : "bg-red-400"}`} />
  );

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] overflow-hidden">
      <div className="p-4 border-b border-[var(--border)]">
        <h2 className="text-lg font-semibold text-[var(--text-primary)]">🛡️ Resilience & Health</h2>
      </div>
      <div className="p-4 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)]">
            <p className="text-[10px] uppercase text-[var(--text-secondary)] font-bold">Uptime</p>
            <p className="text-lg font-mono text-[var(--accent-blue)] mt-1">
              {metrics ? formatUptime(metrics.uptime_seconds) : "---"}
            </p>
          </div>
          <div className="p-3 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)]">
            <p className="text-[10px] uppercase text-[var(--text-secondary)] font-bold">Backup Status</p>
            <p className="text-lg font-bold text-[var(--accent-green)] mt-1">
              {metrics?.backup_status || "SAFE"}
            </p>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between p-2 rounded bg-[var(--bg-primary)]/50 text-xs">
            <span className="text-[var(--text-secondary)]">Gateway Daemon</span>
            <div className="flex items-center gap-2">
              <span className="text-[var(--text-primary)] font-medium">{metrics?.gateway_status || "OK"}</span>
              <StatusLight status={metrics?.gateway_status || "OK"} />
            </div>
          </div>
          <div className="flex items-center justify-between p-2 rounded bg-[var(--bg-primary)]/50 text-xs">
            <span className="text-[var(--text-secondary)]">GitHub API</span>
            <div className="flex items-center gap-2">
              <span className="text-[var(--text-primary)] font-medium">{metrics?.github_status || "OK"}</span>
              <StatusLight status={metrics?.github_status || "OK"} />
            </div>
          </div>
          <div className="flex items-center justify-between p-2 rounded bg-[var(--bg-primary)]/50 text-xs">
            <span className="text-[var(--text-secondary)]">Vercel API</span>
            <div className="flex items-center gap-2">
              <span className="text-[var(--text-primary)] font-medium">{metrics?.vercel_status || "OK"}</span>
              <StatusLight status={metrics?.vercel_status || "OK"} />
            </div>
          </div>
          <div className="flex items-center justify-between p-2 rounded bg-[var(--bg-primary)]/50 text-xs">
            <span className="text-[var(--text-secondary)]">Supabase DB</span>
            <div className="flex items-center gap-2">
              <span className="text-[var(--text-primary)] font-medium">{metrics?.supabase_status || "OK"}</span>
              <StatusLight status={metrics?.supabase_status || "OK"} />
            </div>
          </div>
        </div>

        {metrics?.last_backup_at && (
          <div className="pt-2">
            <p className="text-[10px] text-[var(--text-secondary)] text-center">
              Last backup synced: {new Date(metrics.last_backup_at).toLocaleString()}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
