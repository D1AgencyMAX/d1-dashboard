"use client";

import { useEffect, useState, useCallback } from "react";
import { 
  supabase, Agent, Project, Task, ActivityItem, 
  SystemMetrics, BusinessMetrics, Deployment 
} from "@/lib/supabase";

import StatsCards from "@/components/StatsCards";
import AgentGrid from "@/components/AgentGrid";
import ActivityFeed from "@/components/ActivityFeed";
import CostBreakdown from "@/components/CostBreakdown";
import ProjectsList from "@/components/ProjectsList";
import SystemHealth from "@/components/SystemHealth";
import StatusBar from "@/components/StatusBar";
import BusinessMetricsPanel from "@/components/BusinessMetricsPanel";
import DeploymentPanel from "@/components/DeploymentPanel";

export default function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [businessMetrics, setBusinessMetrics] = useState<BusinessMetrics | null>(null);
  
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [connected, setConnected] = useState(false);
  const [clientMode, setClientMode] = useState(false);
  const [errorCount, setErrorCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      const [
        agentsRes, projectsRes, tasksRes, 
        activitiesRes, metricsRes, businessRes, deploRes
      ] = await Promise.all([
        supabase.from("agents").select("*").order("department").order("name"),
        supabase.from("projects").select("*").order("created_at", { ascending: false }),
        supabase.from("tasks").select("*").order("created_at", { ascending: false }),
        supabase.from("activity_feed").select("*").order("created_at", { ascending: false }).limit(50),
        supabase.from("system_metrics").select("*").order("snapshot_at", { ascending: false }).limit(1).single(),
        supabase.from("business_metrics").select("*").order("updated_at", { ascending: false }).limit(1).single(),
        supabase.from("deployments").select("*").order("created_at", { ascending: false }).limit(5),
      ]);

      if (agentsRes.data) setAgents(agentsRes.data);
      if (projectsRes.data) setProjects(projectsRes.data);
      if (tasksRes.data) setTasks(tasksRes.data);
      if (activitiesRes.data) setActivities(activitiesRes.data);
      if (metricsRes.data) setMetrics(metricsRes.data);
      if (businessRes.data) setBusinessMetrics(businessRes.data);
      if (deploRes.data) setDeployments(deploRes.data);
      
      setLastUpdate(new Date());
      setErrorCount(0);
      setIsLoading(false);
    } catch (e) {
      console.error("Fetch error:", e);
      setErrorCount(prev => prev + 1);
    }
  }, []);

  // Initial fetch
  useEffect(() => { loadData(); }, [loadData]);

  // Realtime & Polling Engine
  useEffect(() => {
    // 1. WebSocket Realtime
    const channel = supabase
      .channel("dashboard-realtime")
      .on("postgres_changes", { event: "*", schema: "public", table: "business_metrics" }, (p) => setBusinessMetrics(p.new as BusinessMetrics))
      .on("postgres_changes", { event: "*", schema: "public", table: "system_metrics" }, (p) => setMetrics(p.new as SystemMetrics))
      .on("postgres_changes", { event: "*", schema: "public", table: "deployments" }, (p) => loadData()) // Refresh all on deploy
      .on("postgres_changes", { event: "*", schema: "public", table: "agents" }, (payload) => {
        setAgents((prev) => {
          if (payload.eventType === "UPDATE") {
            return prev.map((a) => (a.id === (payload.new as Agent).id ? (payload.new as Agent) : a));
          }
          if (payload.eventType === "INSERT") return [...prev, payload.new as Agent];
          return prev;
        });
      })
      .on("postgres_changes", { event: "INSERT", schema: "public", table: "activity_feed" }, (p) => {
        setActivities((prev) => [p.new as ActivityItem, ...prev].slice(0, 50));
      })
      .subscribe((status) => {
        setConnected(status === "SUBSCRIBED");
      });

    // 2. Resilience Polling (every 5 seconds)
    const pollInterval = setInterval(() => {
      loadData();
    }, 5000);

    return () => {
      supabase.removeChannel(channel);
      clearInterval(pollInterval);
    };
  }, [loadData]);

  if (errorCount > 3) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)] flex flex-col items-center justify-center font-mono">
        <div className="w-2 h-2 rounded-full bg-red-500 animate-ping mb-4" />
        <h1 className="text-red-500 font-bold text-xl mb-2">SYSTEM_CONNECTION_FAILURE</h1>
        <p className="text-[var(--text-secondary)] text-sm mb-6">Live data stream unavailable. Attempting automatic failover...</p>
        <div className="px-4 py-2 border border-red-500/30 bg-red-500/10 text-red-400 text-[10px] rounded">
          RETRY_ATTEMPT_{errorCount}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <StatusBar metrics={metrics} agents={agents} clientMode={clientMode} />
      
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--bg-primary)]/90 backdrop-blur-xl">
        <div className="max-w-[1600px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-blue-500/20">D1</div>
                <div>
                  <h1 className="text-lg font-bold text-[var(--text-primary)] tracking-tight">DIGITAL ONE AGENCY</h1>
                  <p className="text-[10px] text-[var(--text-secondary)] font-mono flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                    LIVE_CONTROL_SYSTEM_v2.1_PROD
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-6">
              <div className="flex items-center gap-3 bg-[var(--bg-secondary)] p-1 rounded-lg border border-[var(--border)] shadow-inner">
                <button 
                  onClick={() => setClientMode(false)}
                  className={`px-3 py-1.5 text-[10px] font-bold rounded-md transition-all ${!clientMode ? 'bg-[var(--bg-card)] text-[var(--text-primary)] shadow-sm' : 'text-gray-500 hover:text-gray-300'}`}
                >
                  ADMIN_CMD
                </button>
                <button 
                  onClick={() => setClientMode(true)}
                  className={`px-3 py-1.5 text-[10px] font-bold rounded-md transition-all ${clientMode ? 'bg-[var(--bg-card)] text-[var(--text-primary)] shadow-sm' : 'text-gray-500 hover:text-gray-300'}`}
                >
                  CLIENT_VIEW
                </button>
              </div>

              <div className="flex items-center gap-4 border-l border-[var(--border)] pl-6">
                <div className="flex flex-col items-end">
                  <span className={`text-[10px] font-bold ${connected ? 'text-green-500' : 'text-yellow-500'}`}>
                    {connected ? "STREAM: ACTIVE" : "STREAM: POLLING"}
                  </span>
                  <span className="text-[9px] font-mono text-[var(--text-secondary)] uppercase">
                    Sync: {lastUpdate.toLocaleTimeString([], { hour12: false })}
                  </span>
                </div>
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
            <DeploymentPanel deployments={deployments} />
            {!clientMode && <CostBreakdown agents={agents} />}
            <ProjectsList projects={projects} />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[var(--border)] mt-12 bg-[#05050a] py-6">
        <div className="max-w-[1600px] mx-auto px-6 flex items-center justify-between text-[10px] text-gray-500 font-mono">
          <div className="flex items-center gap-4">
            <span>© 2026 DIGITAL ONE AGENCY</span>
            <span>SYSTEM_LOC: AU_BRISBANE</span>
          </div>
          <div className="flex items-center gap-6">
            <span className="text-blue-500">ENGINE: OPENCLAW_CORE</span>
            <span className="text-green-500">UPTIME: {metrics ? (metrics.uptime_seconds / 3600).toFixed(1) : '0'}H</span>
            <span className="text-purple-500">TASKS: {tasks.length}</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
