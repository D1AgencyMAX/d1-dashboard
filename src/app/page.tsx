"use client";

import { useEffect, useState } from "react";
import { supabase, Agent, Project, Task, ActivityItem } from "@/lib/supabase";
import StatsCards from "@/components/StatsCards";
import AgentGrid from "@/components/AgentGrid";
import ActivityFeed from "@/components/ActivityFeed";
import CostBreakdown from "@/components/CostBreakdown";
import ProjectsList from "@/components/ProjectsList";

export default function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [connected, setConnected] = useState(false);

  // Initial data fetch
  useEffect(() => {
    async function loadData() {
      const [agentsRes, projectsRes, tasksRes, activitiesRes] = await Promise.all([
        supabase.from("agents").select("*").order("department").order("name"),
        supabase.from("projects").select("*").order("created_at", { ascending: false }),
        supabase.from("tasks").select("*").order("created_at", { ascending: false }),
        supabase.from("activity_feed").select("*").order("created_at", { ascending: false }).limit(50),
      ]);

      if (agentsRes.data) setAgents(agentsRes.data);
      if (projectsRes.data) setProjects(projectsRes.data);
      if (tasksRes.data) setTasks(tasksRes.data);
      if (activitiesRes.data) setActivities(activitiesRes.data);
      setLastUpdate(new Date());
    }

    loadData();
  }, []);

  // Realtime subscriptions
  useEffect(() => {
    const channel = supabase
      .channel("dashboard-realtime")
      .on("postgres_changes", { event: "*", schema: "public", table: "agents" }, (payload) => {
        setAgents((prev) => {
          if (payload.eventType === "UPDATE") {
            return prev.map((a) => (a.id === (payload.new as Agent).id ? (payload.new as Agent) : a));
          }
          if (payload.eventType === "INSERT") return [...prev, payload.new as Agent];
          if (payload.eventType === "DELETE") return prev.filter((a) => a.id !== (payload.old as Agent).id);
          return prev;
        });
        setLastUpdate(new Date());
      })
      .on("postgres_changes", { event: "*", schema: "public", table: "projects" }, (payload) => {
        setProjects((prev) => {
          if (payload.eventType === "UPDATE") {
            return prev.map((p) => (p.id === (payload.new as Project).id ? (payload.new as Project) : p));
          }
          if (payload.eventType === "INSERT") return [payload.new as Project, ...prev];
          if (payload.eventType === "DELETE") return prev.filter((p) => p.id !== (payload.old as Project).id);
          return prev;
        });
        setLastUpdate(new Date());
      })
      .on("postgres_changes", { event: "*", schema: "public", table: "tasks" }, (payload) => {
        setTasks((prev) => {
          if (payload.eventType === "UPDATE") {
            return prev.map((t) => (t.id === (payload.new as Task).id ? (payload.new as Task) : t));
          }
          if (payload.eventType === "INSERT") return [payload.new as Task, ...prev];
          if (payload.eventType === "DELETE") return prev.filter((t) => t.id !== (payload.old as Task).id);
          return prev;
        });
        setLastUpdate(new Date());
      })
      .on("postgres_changes", { event: "INSERT", schema: "public", table: "activity_feed" }, (payload) => {
        setActivities((prev) => [payload.new as ActivityItem, ...prev].slice(0, 50));
        setLastUpdate(new Date());
      })
      .subscribe((status) => {
        setConnected(status === "SUBSCRIBED");
      });

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--bg-primary)]/80 backdrop-blur-xl">
        <div className="max-w-[1600px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg">
                  D1
                </div>
                <div>
                  <h1 className="text-lg font-bold text-[var(--text-primary)]">Digital One Agency</h1>
                  <p className="text-xs text-[var(--text-secondary)]">Command Center</p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Connection status */}
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${connected ? "bg-green-400 animate-pulse" : "bg-red-400"}`} />
                <span className="text-xs text-[var(--text-secondary)]">
                  {connected ? "Live" : "Connecting..."}
                </span>
              </div>

              {/* Last update */}
              <span className="text-xs text-[var(--text-secondary)]">
                Updated: {lastUpdate.toLocaleTimeString()}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-[1600px] mx-auto px-6 py-6 space-y-6">
        {/* Stats */}
        <StatsCards agents={agents} tasks={tasks} />

        {/* Main grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Agent grid - takes 2 cols */}
          <div className="lg:col-span-2">
            <AgentGrid agents={agents} />
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <ActivityFeed activities={activities} />
            <CostBreakdown agents={agents} />
            <ProjectsList projects={projects} />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[var(--border)] mt-8">
        <div className="max-w-[1600px] mx-auto px-6 py-4 flex items-center justify-between text-xs text-[var(--text-secondary)]">
          <span>Digital One Agency © {new Date().getFullYear()} — Powered by Max & Team</span>
          <span>⚡ {agents.length} agents • 3 providers • Realtime enabled</span>
        </div>
      </footer>
    </div>
  );
}
