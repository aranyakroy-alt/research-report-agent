export type AgentEvent = {
  type:
    | 'goal_set'
    | 'tool_selected'
    | 'cache_hit'
    | 'tool_result'
    | 'evaluation'
    | 'gap_found'
    | 'dimension_answered'
    | 'tool_failure'
    | 'dimensions_ready'
    | 'report_generating'
    | 'report_ready'
    | 'complete'
    | 'error';
  data: Record<string, any>;
};

export type RunResult = {
  brief_path: string;
  scenario: string;
  cost_summary: {
    total_cost_usd: number;
    calls_by_component: Record<string, { cost: number; calls: number }>;
  };
  elapsed_seconds: number;
};

export type HistoryRow = {
  company: string;
  scenario: string;
  cost_usd: number;
  elapsed_seconds: number;
  completeness: number;
  stance: string;
  confidence: number;
  run_date: string;
  brief_path: string;
};

export type PhaseId = 'goal' | 'dimensions' | 'react' | 'report';

export type DimStatus = 'pending' | 'active' | 'answered' | 'failed';
