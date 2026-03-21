"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertsCard,
  AdsCard,
  CapacityCard,
  DashboardHeader,
  DealsTable,
  HeroMetrics,
  MarginsCard,
  PipelineCard,
  QuickActionsCard,
  RevenueChart,
  RevenueTargetsCard,
} from "@/components/dashboard";
import { dashboardFallback, DashboardSnapshot } from "@/lib/dashboard";
import { supabase } from "@/lib/supabase";

export default function Page() {
  const [snapshot, setSnapshot] = useState<DashboardSnapshot>(dashboardFallback);
  const [connected, setConnected] = useState(false);
  const [updatedAt, setUpdatedAt] = useState(new Date());

  const loadSnapshot = useCallback(async () => {
    try {
      const { data } = await supabase.from("dashboard_snapshots").select("payload, updated_at").order("updated_at", { ascending: false }).limit(1).maybeSingle();
      if (data?.payload) {
        setSnapshot(data.payload as DashboardSnapshot);
        setUpdatedAt(data.updated_at ? new Date(data.updated_at) : new Date());
      } else {
        setUpdatedAt(new Date());
      }
    } catch {
      setSnapshot(dashboardFallback);
      setUpdatedAt(new Date());
    }
  }, []);

  useEffect(() => {
    loadSnapshot();
  }, [loadSnapshot]);

  useEffect(() => {
    const channel = supabase
      .channel("d1-dashboard-live")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "dashboard_snapshots" },
        (payload) => {
          const next = payload.new as { payload?: DashboardSnapshot; updated_at?: string };
          if (next?.payload) {
            setSnapshot(next.payload);
            setUpdatedAt(next.updated_at ? new Date(next.updated_at) : new Date());
          } else {
            void loadSnapshot();
          }
        },
      )
      .subscribe((status) => {
        setConnected(status === "SUBSCRIBED");
      });

    const interval = window.setInterval(() => {
      if (!connected) {
        void loadSnapshot();
      }
    }, 10000);

    return () => {
      window.clearInterval(interval);
      void supabase.removeChannel(channel);
    };
  }, [connected, loadSnapshot]);

  const headline = useMemo(() => snapshot.headline, [snapshot]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <DashboardHeader connected={connected} updatedAt={updatedAt} />
      <main className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <HeroMetrics {...headline} />

        <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <RevenueChart points={snapshot.revenueSeries} />
          <RevenueTargetsCard items={snapshot.revenueTargets} />
        </div>

        <div className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
          <PipelineCard stages={snapshot.pipeline} />
          <DealsTable deals={snapshot.deals} />
        </div>

        <div className="grid gap-6 lg:grid-cols-2 xl:grid-cols-4">
          <AdsCard channels={snapshot.adChannels} />
          <CapacityCard items={snapshot.capacity} />
          <MarginsCard items={snapshot.margins} />
          <AlertsCard items={snapshot.alerts} />
        </div>

        <QuickActionsCard items={snapshot.quickActions} />
      </main>
    </div>
  );
}
