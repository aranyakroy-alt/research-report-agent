import React, { useMemo } from 'react';
import { AgentEvent, RunResult, DimStatus } from '../types';
import { MetricCard } from './MetricCard';
import { DimensionGrid } from './DimensionGrid';
import { VerdictBar } from './VerdictBar';
import { BriefSection } from './BriefSection';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface ResultsPanelProps {
  result: RunResult | null;
  events: AgentEvent[];
  scenario: string;
}

const BRIEF_SECTIONS = [
  'Business Overview',
  'Key Financials',
  'Recent News & Sentiment',
  'Key Risks',
  'Sector Outlook',
  'Investment Thesis',
];

function parseSections(md: string): Record<string, string> {
  const out: Record<string, string> = {};
  let current = '';
  for (const line of md.split('\n')) {
    const h2 = line.match(/^##\s+(.+)/);
    if (h2) {
      current = h2[1].trim();
      out[current] = '';
    } else if (current) {
      out[current] = (out[current] ?? '') + line + '\n';
    }
  }
  return out;
}

function extractStance(md: string): { stance: string; confidence: number } {
  // Match **Weighted Stance: HOLD (Confidence: 35%)** — with or without bold markers
  const m = md.match(/Weighted Stance:\s*\*{0,2}(\w+)\*{0,2}\s*\(Confidence:\s*(\d+)%\)/i);
  if (m) return { stance: m[1], confidence: parseInt(m[2]) / 100 };
  return { stance: 'UNKNOWN', confidence: 0 };
}

export const ResultsPanel: React.FC<ResultsPanelProps> = ({ result, events, scenario }) => {
  const dimStatus = useMemo(() => {
    const map: Record<string, DimStatus> = {};
    for (const e of events) {
      if (e.type === 'tool_selected')      map[e.data.dimension] = map[e.data.dimension] === 'answered' ? 'answered' : 'active';
      if (e.type === 'evaluation')         map[e.data.dimension] = map[e.data.dimension] === 'answered' ? 'answered' : 'active';
      if (e.type === 'dimension_answered') map[e.data.dimension] = 'answered';
      if (e.type === 'tool_failure' && map[e.data.dimension] !== 'answered') map[e.data.dimension] = 'failed';
      // Gap dimensions appear from tool_selected events with D7+ ids — already handled above
    }
    return map;
  }, [events]);

  const [briefText, setBriefText] = React.useState('');

  // Clear brief when a new run starts (events array is reset to empty)
  React.useEffect(() => {
    if (events.length === 0) setBriefText('');
  }, [events.length === 0]);

  // Try to load brief as soon as report_ready event fires (has the path)
  // AND again when result arrives (complete event)
  const briefPath = React.useMemo(() => {
    if (result?.brief_path) return result.brief_path;
    const reportReady = events.find(e => e.type === 'report_ready');
    return reportReady?.data?.path ?? null;
  }, [result?.brief_path, events]);

  React.useEffect(() => {
    if (!briefPath) return;
    fetch(`${API_BASE}/api/brief?path=${encodeURIComponent(briefPath)}`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.text();
      })
      .then(setBriefText)
      .catch(() => {});
  }, [briefPath]);

  const sections = useMemo(() => parseSections(briefText), [briefText]);
  const { stance, confidence } = useMemo(() => extractStance(briefText), [briefText]);

  const cost = result?.cost_summary.total_cost_usd ?? 0;
  const time = result?.elapsed_seconds ?? 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div style={{
        padding: '10px 16px', borderBottom: '0.5px solid var(--border)',
        display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0,
      }}>
        <span style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-tertiary)', fontWeight: 500 }}>
          Results
        </span>
        {scenario && (
          <span style={{
            fontSize: 11, background: 'var(--info-bg)', color: 'var(--info-text)',
            borderRadius: 4, padding: '2px 8px',
          }}>{scenario}</span>
        )}
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: 12, display: 'flex', flexDirection: 'column', gap: 12 }}>
        {/* Metrics */}
        <div style={{ display: 'flex', gap: 8 }}>
          <MetricCard label="Cost" value={`$${cost.toFixed(4)}`} />
          <MetricCard label="Time" value={`${time}s`} />
          <MetricCard label="Dimensions" value={`${Object.values(dimStatus).filter(s => s === 'answered').length}/${Object.keys(dimStatus).length || 6}`} />
        </div>

        {/* Dimension grid */}
        <div>
          <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-tertiary)', marginBottom: 6 }}>
            Dimensions
          </div>
          <DimensionGrid dims={dimStatus} />
        </div>

        {/* Verdict */}
        {result && (
          <div>
            <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-tertiary)', marginBottom: 6 }}>
              Verdict
            </div>
            <VerdictBar stance={stance} confidence={confidence} />
          </div>
        )}

        {/* Brief sections */}
        {briefText && (
          <div>
            <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-tertiary)', marginBottom: 6 }}>
              Brief
            </div>
            {BRIEF_SECTIONS.map(sec => (
              <BriefSection key={sec} title={sec} content={(sections[sec] ?? '').trim() || '—'} />
            ))}
            {result?.brief_path && (
              <a
                href={`${API_BASE}/api/brief?path=${encodeURIComponent(result.brief_path)}`}
                target="_blank" rel="noreferrer"
                style={{ fontSize: 12, color: 'var(--info-text)', display: 'block', marginTop: 8 }}
              >
                View full brief ↗
              </a>
            )}
          </div>
        )}

        {!result && (
          <div style={{ color: 'var(--text-tertiary)', fontSize: 13, textAlign: 'center', marginTop: 40 }}>
            Results will appear here after the run completes.
          </div>
        )}
      </div>
    </div>
  );
};
