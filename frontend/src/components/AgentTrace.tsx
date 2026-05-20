import React, { useMemo } from 'react';
import { AgentEvent } from '../types';
import { PhaseBlock } from './PhaseBlock';

interface AgentTraceProps {
  events: AgentEvent[];
  status: 'idle' | 'running' | 'complete' | 'error';
}

type PhaseState = 'pending' | 'active' | 'done';

const REACT_EVENTS = new Set(['tool_selected','cache_hit','tool_result','evaluation','gap_found','dimension_answered','tool_failure']);

export const AgentTrace: React.FC<AgentTraceProps> = ({ events, status }) => {
  const running = status === 'running';
  const done    = status === 'complete' || status === 'error';

  const hasGoal   = events.some(e => e.type === 'goal_set');
  const hasDims   = events.some(e => e.type === 'dimensions_ready');
  const hasReact  = events.some(e => REACT_EVENTS.has(e.type));
  const hasReportGen = events.some(e => e.type === 'report_generating');
  const hasReport = events.some(e => e.type === 'report_ready');

  const phases: { id: string; icon: string; title: string; state: PhaseState; evts: AgentEvent[] }[] = useMemo(() => [
    {
      id: 'goal',
      icon: '1', title: 'Goal setter',
      state: hasGoal ? 'done' : running ? 'active' : 'pending',
      evts: events.filter(e => e.type === 'goal_set'),
    },
    {
      id: 'dims',
      icon: '2', title: 'Dimension generator',
      state: hasDims ? 'done' : hasGoal ? 'active' : 'pending',
      evts: events.filter(e => e.type === 'dimensions_ready'),
    },
    {
      id: 'react',
      icon: '3', title: 'ReAct loop',
      state: hasReportGen ? 'done' : hasReact ? 'active' : 'pending',
      evts: events.filter(e => REACT_EVENTS.has(e.type)),
    },
    {
      id: 'report',
      icon: '4', title: 'Report generator',
      state: hasReport ? 'done' : hasReportGen ? 'active' : 'pending',
      evts: events.filter(e => e.type === 'report_ready' || e.type === 'report_generating'),
    },
  ], [events, running, done, hasGoal, hasDims, hasReact, hasReportGen, hasReport]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Panel header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '10px 16px', borderBottom: '0.5px solid var(--border)',
        flexShrink: 0,
      }}>
        <span style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-tertiary)', fontWeight: 500 }}>
          Agent trace
        </span>
        {running && (
          <span style={{
            width: 8, height: 8, borderRadius: '50%', background: '#16a34a',
            animation: 'pulse 1.5s infinite', display: 'inline-block',
          }} />
        )}
      </div>

      {/* Phase blocks */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 12 }}>
        {status === 'idle' ? (
          <div style={{ color: 'var(--text-tertiary)', fontSize: 13, textAlign: 'center', marginTop: 40 }}>
            Enter a company and click Run ↗
          </div>
        ) : (
          phases.map(p => (
            <PhaseBlock
              key={p.id}
              icon={p.icon}
              title={p.title}
              meta={p.evts.length > 0 ? `${p.evts.length} events` : undefined}
              state={p.state}
              events={p.evts}
            />
          ))
        )}
      </div>
    </div>
  );
};
