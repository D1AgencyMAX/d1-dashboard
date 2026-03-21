import { 
  Campaign, 
  PipelineStage, 
  AgentCapacity, 
  ClientProfit, 
  Agent, 
  LeadFlowMetrics, 
  Alert, 
  RevenueHistory,
  SystemMetrics,
  BusinessMetrics
} from './src/lib/supabase';

// ========================================
// TypeScript Types for D1 Dashboard Redesign
// ========================================
// Add these to src/lib/supabase.ts or create a separate types.ts file

export interface RevenueDataPoint {
  month: Date;
  actual?: number; // Historical revenue
  projected?: number; // Forecasted revenue
  confidence_high?: number; // Upper confidence bound
  confidence_low?: number; // Lower confidence bound
}

// ========================================
// Component Props Interfaces
// ========================================

export interface RevenueCounterProps {
  value: number;
  target?: number;
  trend24h?: number[];
  currency?: string;
  onIncrement?: () => void;
}

export interface ClientPipelineFunnelProps {
  stages: PipelineStage[];
  onStageClick?: (stage: string) => void;
  loading?: boolean;
}

export interface CampaignDashboardProps {
  campaigns: Campaign[];
  onCampaignClick?: (id: string) => void;
  loading?: boolean;
}

export interface TeamCapacityHeatmapProps {
  agents: AgentCapacity[];
  weekStartDate?: Date;
  onCellClick?: (agentId: string, date: Date) => void;
}

export interface ProfitMarginTrackerProps {
  clients: ClientProfit[];
  expandedClientId?: string;
  onClientClick?: (id: string) => void;
  loading?: boolean;
}

export interface AIWorkerStatusProps {
  agents: Agent[]; // Existing Agent type
  fleetHealth: number; // 0-100
  avgLoad: number;
  onAgentClick?: (id: string) => void;
}

export interface LeadFlowLiveProps {
  metrics: LeadFlowMetrics;
  loading?: boolean;
}

export interface RevenueProjectionProps {
  data: RevenueDataPoint[];
  target?: number;
  thisMonthRevenue: number;
  thisMonthProjection: number;
  nextMonthProjection: number;
  loading?: boolean;
}

export interface AlertFeedProps {
  alerts: Alert[];
  onDismiss?: (id: string) => void;
  onAlertClick?: (alert: Alert) => void;
  maxItems?: number;
}

export interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  onClick: () => void;
  shortcut?: string;
}

export interface QuickActionsBarProps {
  actions: QuickAction[];
  position?: 'bottom-right' | 'bottom-left';
}

// ========================================
// Utility Types
// ========================================

export type StatusType = 'active' | 'idle' | 'error' | 'warning';
export type PlatformType = 'meta' | 'google' | 'tiktok';
export type AlertType = 'urgent' | 'warning' | 'info';
export type CapacityStatus = 'available' | 'busy' | 'overloaded';

// ========================================
// Supabase Query Types
// ========================================

export interface SupabaseQueryOptions {
  from?: Date;
  to?: Date;
  limit?: number;
  offset?: number;
}

export interface DashboardData {
  campaigns: Campaign[];
  leadFlow: LeadFlowMetrics;
  pipeline: PipelineStage[];
  alerts: Alert[];
  revenueHistory: RevenueHistory[];
  agentCapacity: AgentCapacity[];
  clientProfits: ClientProfit[];
  agents: Agent[]; // Existing type
  systemMetrics?: SystemMetrics; // Existing type
  businessMetrics?: BusinessMetrics; // Existing type
}

// ========================================
// Animation Types (for Framer Motion)
// ========================================

export interface AnimationConfig {
  initial?: object;
  animate?: object;
  exit?: object;
  transition?: object;
}

export interface SpringConfig {
  type: 'spring';
  stiffness: number;
  damping: number;
  mass?: number;
}

// ========================================
// Chart Data Types
// ========================================

export interface ChartDataPoint {
  label: string;
  value: number;
  color?: string;
  metadata?: any;
}

export interface LineChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    color: string;
    fill?: boolean;
  }>;
}

export interface BarChartData {
  labels: string[];
  values: number[];
  colors?: string[];
  horizontal?: boolean;
}

export interface SparklineData {
  values: number[];
  color?: string;
  height?: number;
}

// ========================================
// API Response Types
// ========================================

export interface ApiResponse<T> {
  data?: T;
  error?: {
    message: string;
    code?: string;
  };
  loading?: boolean;
}

export interface RealtimePayload<T> {
  eventType: 'INSERT' | 'UPDATE' | 'DELETE';
  new: T;
  old: T;
}
