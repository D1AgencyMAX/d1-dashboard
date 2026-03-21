import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export interface Campaign {
  id: string;
  platform: 'meta' | 'google' | 'tiktok';
  name: string;
  client_id?: string;
  status: 'active' | 'paused' | 'completed';
  spend_usd: number;
  budget_usd: number;
  impressions: number;
  clicks: number;
  ctr: number;
  roas: number;
  target_roas: number;
  last_updated: string;
  created_at: string;
}

export interface LeadFlow {
  id: string;
  timestamp: string;
  new_leads: number;
  calls_booked: number;
  consultations_held: number;
  deals_closed: number;
}

export interface LeadFlowMetrics {
  leads_today: number;
  calls_today: number;
  consultations_today: number;
  closes_today: number;
  lead_to_call_rate: number;
  call_to_consultation_rate: number;
  consultation_to_close_rate: number;
  hourly_data: LeadFlow[];
}

export interface Pipeline {
  id: string;
  client_name: string;
  client_id?: string;
  stage: 'discovery' | 'qualified' | 'proposal' | 'won' | 'lost';
  value_usd: number;
  entered_at: string;
  expected_close_date?: string;
  probability: number;
  notes?: string;
  updated_at: string;
}

export interface PipelineStage {
  stage: 'discovery' | 'qualified' | 'proposal' | 'won';
  count: number;
  value_usd: number;
  clients: Array<{
    name: string;
    value: number;
    entered_at: string;
    expected_close_date?: string;
  }>;
  conversion_rate?: number;
}

export interface Alert {
  id: string;
  type: 'urgent' | 'warning' | 'info';
  title: string;
  description?: string;
  assigned_to?: string;
  action_url?: string;
  dismissed: boolean;
  created_at: string;
}

export interface RevenueHistory {
  id: string;
  month: string;
  revenue_usd: number;
  created_at: string;
}

export interface RevenueDataPoint {
  month: Date;
  actual?: number;
  projected?: number;
  confidence_high?: number;
  confidence_low?: number;
}

export interface AgentCapacity {
  id: string;
  agent_id: string;
  agent_name: string;
  date: string;
  project_count: number;
  status: 'available' | 'busy' | 'overloaded';
  projects: string[];
  created_at: string;
  updated_at: string;
}

export interface ClientProfit {
  id: string;
  client_id?: string;
  client_name: string;
  revenue_usd: number;
  labor_cost_usd: number;
  tools_cost_usd: number;
  ads_cost_usd: number;
  profit_usd: number;
  margin_percent: number;
  updated_at: string;
}

export type Agent = {
  id: string;
  name: string;
  role: string;
  department: string;
  model: string;
  status: 'idle' | 'working' | 'error' | 'offline';
  current_task: string | null;
  tasks_completed: number;
  tokens_used: number;
  cost_usd: number;
  last_active: string | null;
  last_heartbeat_at: string | null;
};

export type Project = {
  id: string;
  name: string;
  client: string | null;
  status: 'planning' | 'active' | 'paused' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  budget_usd: number | null;
  spent_usd: number;
  description: string | null;
  started_at: string | null;
  deadline: string | null;
  completed_at: string | null;
};

export type Task = {
  id: string;
  project_id: string | null;
  agent_id: string | null;
  title: string;
  description: string | null;
  status: 'pending' | 'in_progress' | 'review' | 'completed' | 'failed';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  tokens_used: number;
  cost_usd: number;
  started_at: string | null;
  completed_at: string | null;
};

export type ActivityItem = {
  id: string;
  agent_id: string | null;
  project_id: string | null;
  event_type: string;
  title: string;
  description: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type CostLogEntry = {
  id: string;
  agent_id: string | null;
  project_id: string | null;
  provider: string;
  model: string;
  tokens_input: number;
  tokens_output: number;
  cost_usd: number;
  created_at: string;
};

export type SystemMetrics = {
  id: string;
  total_agents_active: number;
  total_tasks_running: number;
  total_cost_usd: number;
  tokens_used: number;
  backup_status: string | null;
  last_backup_at: string | null;
  uptime_seconds: number;
  gateway_status: string | null;
  github_status: string | null;
  vercel_status: string | null;
  supabase_status: string | null;
  snapshot_at: string;
};

export type BusinessMetrics = {
  id: string;
  leads_today: number;
  conversion_rate: number;
  revenue_total: number;
  pipeline_value: number;
  updated_at: string;
};

export type AgentLog = {
  id: string;
  agent_id: string;
  level: 'info' | 'warn' | 'error' | 'critical';
  message: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type Deployment = {
  id: string;
  name: string;
  status: string;
  url: string | null;
  created_at: string;
  inspector_url: string | null;
};

export type ProviderBalance = {
  id: string;
  provider_name: string;
  balance_usd: number;
  alert_threshold: number;
  last_updated: string;
};
