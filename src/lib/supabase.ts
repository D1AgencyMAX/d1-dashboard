import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

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
