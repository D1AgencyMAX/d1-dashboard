"use client";

const statusConfig = {
  idle: { color: "bg-gray-500/20 text-gray-400 border-gray-500/30", dot: "bg-gray-400" },
  working: { color: "bg-blue-500/20 text-blue-400 border-blue-500/30", dot: "bg-blue-400 animate-pulse" },
  error: { color: "bg-red-500/20 text-red-400 border-red-500/30", dot: "bg-red-400" },
  offline: { color: "bg-gray-700/20 text-gray-500 border-gray-700/30", dot: "bg-gray-600" },
  // Project/task statuses
  planning: { color: "bg-purple-500/20 text-purple-400 border-purple-500/30", dot: "bg-purple-400" },
  active: { color: "bg-green-500/20 text-green-400 border-green-500/30", dot: "bg-green-400 animate-pulse" },
  paused: { color: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30", dot: "bg-yellow-400" },
  completed: { color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30", dot: "bg-emerald-400" },
  cancelled: { color: "bg-gray-500/20 text-gray-400 border-gray-500/30", dot: "bg-gray-400" },
  pending: { color: "bg-gray-500/20 text-gray-400 border-gray-500/30", dot: "bg-gray-400" },
  in_progress: { color: "bg-blue-500/20 text-blue-400 border-blue-500/30", dot: "bg-blue-400 animate-pulse" },
  review: { color: "bg-amber-500/20 text-amber-400 border-amber-500/30", dot: "bg-amber-400" },
  failed: { color: "bg-red-500/20 text-red-400 border-red-500/30", dot: "bg-red-400" },
};

export default function StatusBadge({ status }: { status: string }) {
  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.idle;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${config.color}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
      {status.replace("_", " ")}
    </span>
  );
}
