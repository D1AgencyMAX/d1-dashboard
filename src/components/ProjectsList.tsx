"use client";

import { Project } from "@/lib/supabase";
import StatusBadge from "./StatusBadge";

const priorityColors: Record<string, string> = {
  urgent: "text-red-400",
  high: "text-orange-400",
  medium: "text-yellow-400",
  low: "text-gray-400",
};

export default function ProjectsList({ projects }: { projects: Project[] }) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] overflow-hidden">
      <div className="p-4 border-b border-[var(--border)] flex items-center justify-between">
        <h2 className="text-lg font-semibold text-[var(--text-primary)]">📋 Projects</h2>
        <span className="text-xs text-[var(--text-secondary)] bg-[var(--bg-primary)] px-2 py-1 rounded-full">
          {projects.filter((p) => p.status === "active").length} active
        </span>
      </div>
      <div className="divide-y divide-[var(--border)] max-h-[400px] overflow-y-auto">
        {projects.length === 0 ? (
          <div className="p-8 text-center text-[var(--text-secondary)]">
            <p className="text-3xl mb-2">📭</p>
            <p className="text-sm">No projects yet — ready for the first client</p>
          </div>
        ) : (
          projects.map((project) => (
            <div key={project.id} className="p-4 hover:bg-[var(--bg-card-hover)] transition-colors">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">{project.name}</h3>
                  {project.client && <p className="text-xs text-[var(--text-secondary)]">{project.client}</p>}
                </div>
                <StatusBadge status={project.status} />
              </div>
              {project.description && (
                <p className="text-xs text-[var(--text-secondary)] mb-2 line-clamp-2">{project.description}</p>
              )}
              <div className="flex items-center gap-4 text-xs">
                <span className={`font-medium ${priorityColors[project.priority]}`}>
                  {project.priority.toUpperCase()}
                </span>
                {project.budget_usd && (
                  <span className="text-[var(--text-secondary)]">
                    ${Number(project.spent_usd || 0).toFixed(0)} / ${Number(project.budget_usd).toFixed(0)}
                  </span>
                )}
                {project.deadline && (
                  <span className="text-[var(--text-secondary)]">
                    Due: {new Date(project.deadline).toLocaleDateString()}
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
