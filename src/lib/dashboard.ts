export type TrendDirection = "up" | "down" | "flat";

export type RevenueTarget = {
  period: "daily" | "weekly" | "monthly";
  target: number;
  actual: number;
};

export type FunnelStage = {
  id: string;
  label: string;
  count: number;
  value: number;
  conversionFromPrev?: number;
};

export type Deal = {
  id: string;
  company: string;
  source: string;
  owner: string;
  value: number;
  stage: "qualified" | "meeting" | "proposal" | "negotiation" | "won";
  probability: number;
  closeDate: string;
  health: "strong" | "watch" | "risk";
};

export type AdChannel = {
  id: string;
  platform: "Meta" | "Google";
  spend: number;
  leads: number;
  cpl: number;
  roas: number;
  trend: TrendDirection;
};

export type CapacityItem = {
  id: string;
  name: string;
  role: string;
  utilisation: number;
  focus: string;
  status: "available" | "busy" | "stretched";
};

export type MarginItem = {
  id: string;
  client: string;
  project: string;
  revenue: number;
  cost: number;
  margin: number;
  status: "healthy" | "tight" | "loss";
};

export type DashboardAlert = {
  id: string;
  level: "critical" | "warning" | "info";
  title: string;
  detail: string;
  action: string;
};

export type QuickAction = {
  id: string;
  label: string;
  description: string;
  href: string;
};

export type RevenueSeriesPoint = {
  label: string;
  revenue: number;
  target: number;
};

export type DashboardSnapshot = {
  revenueTargets: RevenueTarget[];
  revenueSeries: RevenueSeriesPoint[];
  pipeline: FunnelStage[];
  deals: Deal[];
  adChannels: AdChannel[];
  capacity: CapacityItem[];
  margins: MarginItem[];
  alerts: DashboardAlert[];
  quickActions: QuickAction[];
  headline: {
    weeklyRevenue: number;
    weeklyTarget: number;
    leadsThisWeek: number;
    closeRate: number;
    pipelineValue: number;
    weightedPipeline: number;
    avgDealSize: number;
  };
};

export const dashboardFallback: DashboardSnapshot = {
  headline: {
    weeklyRevenue: 182000,
    weeklyTarget: 200000,
    leadsThisWeek: 56,
    closeRate: 18,
    pipelineValue: 1140000,
    weightedPipeline: 478000,
    avgDealSize: 60000,
  },
  revenueTargets: [
    { period: "daily", target: 28571, actual: 24800 },
    { period: "weekly", target: 200000, actual: 182000 },
    { period: "monthly", target: 800000, actual: 726000 },
  ],
  revenueSeries: [
    { label: "Mon", revenue: 22000, target: 28571 },
    { label: "Tue", revenue: 18000, target: 28571 },
    { label: "Wed", revenue: 32000, target: 28571 },
    { label: "Thu", revenue: 26000, target: 28571 },
    { label: "Fri", revenue: 41000, target: 28571 },
    { label: "Sat", revenue: 21000, target: 28571 },
    { label: "Sun", revenue: 22000, target: 28571 },
  ],
  pipeline: [
    { id: "source", label: "Source", count: 56, value: 3360000 },
    { id: "qualified", label: "Qualified", count: 21, value: 1260000, conversionFromPrev: 37.5 },
    { id: "meeting", label: "Meeting", count: 11, value: 660000, conversionFromPrev: 52.4 },
    { id: "deal", label: "Deal", count: 4, value: 240000, conversionFromPrev: 36.4 },
  ],
  deals: [
    { id: "d1", company: "Northstar Finance", source: "Meta", owner: "Closer", value: 60000, stage: "proposal", probability: 70, closeDate: "2026-03-25", health: "strong" },
    { id: "d2", company: "Urban Legal Group", source: "Referral", owner: "Ken", value: 90000, stage: "negotiation", probability: 85, closeDate: "2026-03-23", health: "strong" },
    { id: "d3", company: "Everwell Health", source: "Google", owner: "Hunter", value: 45000, stage: "meeting", probability: 45, closeDate: "2026-03-28", health: "watch" },
    { id: "d4", company: "Buildwise Projects", source: "Outbound", owner: "Closer", value: 120000, stage: "qualified", probability: 35, closeDate: "2026-04-02", health: "risk" },
    { id: "d5", company: "Apex Mobility", source: "Meta", owner: "Ken", value: 75000, stage: "proposal", probability: 60, closeDate: "2026-03-29", health: "watch" },
  ],
  adChannels: [
    { id: "meta", platform: "Meta", spend: 6200, leads: 39, cpl: 159, roas: 4.8, trend: "up" },
    { id: "google", platform: "Google", spend: 4200, leads: 17, cpl: 247, roas: 3.2, trend: "flat" },
  ],
  capacity: [
    { id: "c1", name: "Ken", role: "Sales / Strategy", utilisation: 84, focus: "Closing 3 proposals", status: "busy" },
    { id: "c2", name: "Atlas", role: "Engineering", utilisation: 72, focus: "CRM + dashboard", status: "busy" },
    { id: "c3", name: "Aura", role: "Design", utilisation: 58, focus: "Landing page polish", status: "available" },
    { id: "c4", name: "Blaze", role: "Paid Media", utilisation: 91, focus: "Meta launch + CPL fixes", status: "stretched" },
    { id: "c5", name: "Closer", role: "Sales", utilisation: 76, focus: "Proposal follow-up", status: "busy" },
  ],
  margins: [
    { id: "m1", client: "Urban Legal Group", project: "AI intake + website", revenue: 90000, cost: 36500, margin: 59.4, status: "healthy" },
    { id: "m2", client: "Northstar Finance", project: "App build", revenue: 60000, cost: 29100, margin: 51.5, status: "healthy" },
    { id: "m3", client: "Everwell Health", project: "Funnel rebuild", revenue: 45000, cost: 25750, margin: 42.8, status: "tight" },
    { id: "m4", client: "Buildwise Projects", project: "CRM migration", revenue: 30000, cost: 31500, margin: -5, status: "loss" },
  ],
  alerts: [
    { id: "a1", level: "critical", title: "2 proposals older than 72h", detail: "Northstar Finance and Apex Mobility need follow-up today.", action: "Update deal" },
    { id: "a2", level: "warning", title: "Google CPL above threshold", detail: "Current CPL is $247 vs $180 target.", action: "Review ads" },
    { id: "a3", level: "info", title: "Blaze at 91% capacity", detail: "Shift campaign reporting to Vector or reduce manual optimisations.", action: "Rebalance work" },
  ],
  quickActions: [
    { id: "q1", label: "Add lead", description: "Capture a new inbound lead", href: "#quick-add-lead" },
    { id: "q2", label: "Book meeting", description: "Create a sales call from qualified lead", href: "#book-meeting" },
    { id: "q3", label: "Update deal", description: "Move a deal stage or probability", href: "#update-deal" },
    { id: "q4", label: "Log ad issue", description: "Flag campaign or tracking problem", href: "#log-ad-issue" },
  ],
};

export const currency = (value: number) =>
  new Intl.NumberFormat("en-AU", {
    style: "currency",
    currency: "AUD",
    maximumFractionDigits: 0,
  }).format(value);

export const percent = (value: number, digits = 0) => `${value.toFixed(digits)}%`;

export const compactCurrency = (value: number) => {
  if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (Math.abs(value) >= 1_000) return `${(value / 1_000).toFixed(0)}K`;
  return value.toFixed(0);
};

export const formatCloseDate = (value: string) =>
  new Date(value).toLocaleDateString("en-AU", {
    day: "numeric",
    month: "short",
  });
