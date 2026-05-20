import React, { useState } from 'react';
import { AgentEvent } from '../types';

interface PhaseBlockProps {
  icon: string;
  title: string;
  meta?: string;
  state: 'pending' | 'active' | 'done';
  events: AgentEvent[];
}

const STANCE_BADGE: Record<string, { bg: string; text: string }> = {
  SUPPORTS:    { bg: 'var(--ok-bg)',      text: 'var(--ok-text)' },
  CONTRADICTS: { bg: 'var(--danger-bg)',  text: 'var(--danger-text)' },
  NEUTRAL:     { bg: 'var(--bg-tertiary)',text: 'var(--text-secondary)' },
};

const TAG_STYLE: Record<string, { bg: string; text: string }> = {
  tool:    { bg: 'var(--info-bg)',    text: 'var(--info-text)' },
  cache:   { bg: 'var(--bg-tertiary)',text: 'var(--text-tertiary)' },
  eval:    { bg: 'var(--warn-bg)',    text: 'var(--warn-text)' },
  gap:     { bg: '#f3e8ff',           text: '#7e22ce' },
  ok:      { bg: 'var(--ok-bg)',      text: 'var(--ok-text)' },
  error:   { bg: 'var(--danger-bg)',  text: 'var(--danger-text)' },
  info:    { bg: 'var(--info-bg)',    text: 'var(--info-text)' },
};

function eventToTrace(ev: AgentEvent): { tag: string; text: string; stance?: string } | null {
  switch (ev.type) {
    case 'goal_set':
      return { tag: 'info', text: `${ev.data.company} · ${ev.data.scenario}` };
    case 'tool_selected':
      return { tag: 'tool', text: `${ev.data.dimension} → ${ev.data.tool}` };
    case 'cache_hit':
      return { tag: 'cache', text: `${ev.data.dimension} cache hit` };
    case 'tool_result': {
      const preview = ev.data.preview ?? '';
      // Show friendly message instead of raw error JSON
      const isError = preview.includes("'error'") || preview.includes('"error"');
      const isEmpty = preview === '[]' || preview === '' || preview === 'None';
      const text = isError
        ? `${ev.data.dimension} → ${ev.data.tool}: no data (private/unknown)`
        : isEmpty
        ? `${ev.data.dimension} → ${ev.data.tool}: no results`
        : `${ev.data.dimension} → ${ev.data.tool}: ${preview.slice(0, 80)}`;
      return { tag: isError || isEmpty ? 'cache' : 'tool', text };
    }
    case 'evaluation':
      return { tag: 'eval', text: `${ev.data.dimension}`, stance: ev.data.stance };
    case 'gap_found':
      return { tag: 'gap', text: ev.data.question?.slice(0, 80) };
    case 'dimension_answered':
      return { tag: 'ok', text: `${ev.data.dimension} answered` };
    case 'tool_failure':
      return { tag: 'error', text: `${ev.data.dimension} failed: ${ev.data.error?.slice(0, 60)}` };
    case 'dimensions_ready':
      return { tag: 'info', text: `${ev.data.count} dimensions generated` };
    case 'report_generating':
      return { tag: 'info', text: 'Generating investment brief…' };
    case 'report_ready':
      return { tag: 'ok', text: `Brief saved` };
    default:
      return null;
  }
}

export const PhaseBlock: React.FC<PhaseBlockProps> = ({ icon, title, meta, state, events }) => {
  const [open, setOpen] = useState(state === 'active');

  // Auto-open when phase becomes active
  React.useEffect(() => {
    if (state === 'active') setOpen(true);
  }, [state]);

  const iconColor = state === 'done' ? 'var(--ok-text)' : state === 'active' ? 'var(--info-text)' : 'var(--text-tertiary)';
  const iconContent = state === 'done' ? '✓' : icon;

  return (
    <div style={{ marginBottom: 4 }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          width: '100%', background: state === 'active' ? 'var(--info-bg)' : 'var(--bg-secondary)',
          border: '0.5px solid var(--border)', borderRadius: 8,
          cursor: 'pointer', padding: '8px 12px',
          display: 'flex', alignItems: 'center', gap: 8, textAlign: 'left',
        }}
      >
        <span style={{
          width: 20, height: 20, borderRadius: '50%', flexShrink: 0,
          background: iconColor, color: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 11, fontWeight: 700,
          animation: state === 'active' ? 'pulse 1.5s infinite' : 'none',
        }}>{iconContent}</span>
        <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', flex: 1 }}>{title}</span>
        {meta && <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{meta}</span>}
        <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{open ? '▲' : '▼'}</span>
      </button>

      {open && events.length > 0 && (
        <div style={{
          margin: '2px 0 0 0', padding: '6px 12px',
          background: 'var(--bg-primary)', border: '0.5px solid var(--border)',
          borderTop: 'none', borderRadius: '0 0 8px 8px',
          maxHeight: 280, overflowY: 'auto',
        }}>
          {events.map((ev, i) => {
            const trace = eventToTrace(ev);
            if (!trace) return null;
            const tagStyle = TAG_STYLE[trace.tag] ?? TAG_STYLE['info'];
            const stanceStyle = trace.stance ? STANCE_BADGE[trace.stance] : null;
            return (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 6, padding: '3px 0', borderBottom: '0.5px solid var(--border)' }}>
                <span style={{
                  background: tagStyle.bg, color: tagStyle.text,
                  borderRadius: 4, padding: '1px 6px', fontSize: 10, flexShrink: 0, marginTop: 1,
                }}>{trace.tag}</span>
                <span style={{ fontSize: 12, color: 'var(--text-secondary)', flex: 1, lineHeight: 1.5 }}>{trace.text}</span>
                {stanceStyle && (
                  <span style={{
                    background: stanceStyle.bg, color: stanceStyle.text,
                    borderRadius: 4, padding: '1px 6px', fontSize: 10, flexShrink: 0, marginTop: 1,
                  }}>{trace.stance}</span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
