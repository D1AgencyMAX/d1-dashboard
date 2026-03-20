"use client";

import { Deployment } from "@/lib/supabase";
import StatusBadge from "./StatusBadge";

export default function DeploymentPanel({ deployments }: { deployments: Deployment[] }) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] overflow-hidden">
      <div className="p-4 border-b border-[var(--border)] flex items-center justify-between">
        <h2 className="text-lg font-semibold text-[var(--text-primary)]">🚢 Deployments</h2>
        <span className="text-[10px] font-mono text-[var(--text-secondary)]">VERCEL PROD</span>
      </div>
      <div className="divide-y divide-[var(--border)] max-h-[300px] overflow-y-auto">
        {deployments.length === 0 ? (
          <div className="p-6 text-center text-[var(--text-secondary)] text-sm">
            No recent deployments detected
          </div>
        ) : (
          deployments.map((d) => (
            <div key={d.id} className="p-3 hover:bg-[var(--bg-card-hover)] transition-colors group">
              <div className="flex items-start justify-between">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-[var(--text-primary)] truncate">{d.name}</p>
                    <StatusBadge status={d.status.toLowerCase()} />
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <a 
                      href={`https://${d.url}`} 
                      target="_blank" 
                      className="text-[10px] text-[var(--accent-blue)] hover:underline truncate"
                    >
                      {d.url}
                    </a>
                    <span className="text-[10px] text-[var(--text-secondary)]">
                      {new Date(d.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
