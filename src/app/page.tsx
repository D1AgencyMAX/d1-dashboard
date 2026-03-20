"use client";

import { useEffect, useState } from "react";
import { supabase, Agent, Project, Task, ActivityItem, SystemMetrics, BusinessMetrics } from "@/lib/supabase";
import StatsCards from "@/components/StatsCards";
import AgentGrid from "@/components/AgentGrid";
import ActivityFeed from "@/components/ActivityFeed";
import CostBreakdown from "@/components/CostBreakdown";
import ProjectsList from "@/components/ProjectsList";
import SystemHealth from "@/components/SystemHealth";
import StatusBar from "@/components/StatusBar";
import BusinessMetricsPanel from "@/components/BusinessMetricsPanel";

export default function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [businessMetrics, setBusinessMetrics] = useState<BusinessMetrics | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [connected, setConnected] = useState(false);
  const [clientMode, setClientMode] = useState(false);

  // Initial data fetch
  useEffect(() => {
    async function loadData() {
      const [agentsRes, projectsRes, tasksRes, activitiesRes, metricsRes, businessRes] = await Promise.all([
        supabase.from("agents").select("*").order("department").order("name"),
        supabase.from("projects").select("*").order("created_at", { ascending: false }),
        supabase.from("tasks").select("*").order("created_at", { ascending: false }),
        supabase.from("activity_feed").select("*").order("created_at", { ascending: false }).limit(50),
        supabase.from("system_metrics").select("*").order("snapshot_at", { ascending: false }).limit(1).single(),
        supabase.from("business_metrics").select("*").order("updated_at", { ascending: false }).limit(1).single(),
      ]);

      if (agentsRes.data) setAgents(agentsRes.data);
      if (projectsRes.data) setProjects(projectsRes.data);
      if (tasksRes.data) setTasks(tasksRes.data);
      if (activitiesRes.data) setActivities(activitiesRes.data);
      if (metricsRes.data) setMetrics(metricsRes.data);
      if (businessRes.data) setBusinessMetrics(businessRes.data);
      setLastUpdate(new Date());
    }

    loadData();
  }, []);

  // Realtime subscriptions
  useEffect(() => {
    const channel = supabase
      .channel("dashboard-realtime")
      .on("postgres_changes", { event: "*", schema: "public", table: "business_metrics" }, (payload) => {
        setBusinessMetrics(payload.new as BusinessMetrics);
        setLastUpdate(new Date());
      })
      .on("postgres_changes", { event: "*", schema: "public", table: "system_metrics" }, (payload) => {
        setMetrics(payload.new as SystemMetrics);
        setLastUpdate(new Date());
      })
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
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <StatusBar metrics={metrics} agents={agents} clientMode={clientMode} />
      
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--bg-primary)]/80 backdrop-blur-xl">
        <div className="max-w-[1600px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-blue-500/20">
                  D1
                </div>
                <div>
                  <h1 className="text-lg font-bold text-[var(--text-primary)]">Digital One Agency</h1>
                  <p className="text-xs text-[var(--text-secondary)] font-mono">OPERATIONAL CONTROL SYSTEM</p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-6">
              <div className="flex items-center gap-3 bg-[var(--bg-secondary)] p-1 rounded-lg border border-[var(--border)]">
                <button 
                  onClick={() => setClientMode(false)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${!clientMode ? 'bg-[var(--bg-card)] text-[var(--text-primary)] shadow-sm' : 'text-[var(--text-secondary)]'}`}
                >
                  ADMIN
                </button>
                <button 
                  onClick={() => setClientMode(true)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${clientMode ? 'bg-[var(--bg-card)] text-[var(--text-primary)] shadow-sm' : 'text-[var(--text-secondary)]'}`}
                >
                  CLIENT
                </button>
              </div>

              <div className="flex items-center gap-4 border-l border-[var(--border)] pl-6">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${connected ? "bg-green-400 animate-pulse" : "bg-red-400"}`} />
                  <span className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-tighter">
                    {connected ? "Stream: Active" : "Stream: Offline"}
                  </span>
                </div>
                <span className="text-xs font-mono text-[var(--text-secondary)]">
                  {lastUpdate.toLocaleTimeString()}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-[1600px] mx-auto px-6 py-8 space-y-8">
        {/* Business Metrics */}
        <BusinessMetricsPanel metrics={businessMetrics} clientMode={clientMode} />
        
        {/* Stats */}
        {!clientMode && <StatsCards agents={agents} tasks={tasks} />}

        {/* Main grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Agent grid - takes 2 cols */}
          <div className="lg:col-span-2">
            <AgentGrid agents={agents} clientMode={clientMode} />
          </div>

          {/* Sidebar */}
          <div className="space-y-8">
            <SystemHealth metrics={metrics} />
            <ActivityFeed activities={activities} />
            {!clientMode && <CostBreakdown agents={agents} />}
            <ProjectsList projects={projects} />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[var(--border)] mt-12 bg-[var(--bg-secondary)]/50">
        <div className="max-w-[1600px] mx-auto px-6 py-6 flex items-center justify-between text-xs text-[var(--text-secondary)]">
          <div className="flex items-center gap-4">
            <span>Digital One Agency © {new Date().getFullYear()}</span>
            <span className="text-[var(--border)]">|</span>
            <span className="font-mono">MAX CONTROL v2.0-PROD</span>
          </div>
          <div className="flex items-center gap-4 font-mono">
            <span className="text-green-500/80">LATENCY: 42ms</span>
            <span className="text-blue-500/80">NODES: 21</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
