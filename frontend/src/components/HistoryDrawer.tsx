import React, { useEffect } from 'react';
import { HistoryRow } from '../types';
import { useHistory } from '../hooks/useHistory';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface HistoryDrawerProps {
  company: string;
  open: boolean;
  onClose: () => void;
  onSelectRun: (row: HistoryRow) => void;
}

const STANCE_STYLE: Record<string, { bg: string; color: string }> = {
  BUY:     { bg: '#e8f5e9', color: '#2e7d32' },
  HOLD:    { bg: '#fff8e1', color: '#f57f17' },
  AVOID:   { bg: '#ffebee', color: '#c62828' },
  UNKNOWN: { bg: '#ededea', color: '#6b6b6b' },
};

export const HistoryDrawer: React.FC<HistoryDrawerProps> = ({ company, open, onClose, onSelectRun }) => {
  const { history, loading, fetchHistory } = useHistory();

  useEffect(() => {
    if (open && company) fetchHistory(company);
  }, [open, company, fetchHistory]);

  const chartData = [...history].reverse().map((r, i) => ({
    name: `${r.scenario} (${r.run_date.slice(0, 10)})`,
    confidence: Math.round((r.confidence ?? 0) * 100),
    idx: i,
  }));

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div onClick={onClose} style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.15)', zIndex: 100,
      }} />

      {/* Drawer */}
      <div style={{
        position: 'fixed', top: 0, right: 0, bottom: 0,
        width: 420, background: 'var(--bg-primary)',
        borderLeft: '0.5px solid var(--border-emphasis)',
        zIndex: 101, display: 'flex', flexDirection: 'column',
        boxShadow: '-8px 0 24px rgba(0,0,0,0.08)',
      }}>
        {/* Drawer header */}
        <div style={{
          padding: '14px 16px', borderBottom: '0.5px solid var(--border)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0,
        }}>
          <span style={{ fontSize: 14, fontWeight: 500 }}>History · {company || 'all'}</span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 18, color: 'var(--text-tertiary)' }}>✕</button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: 12 }}>
          {loading && <div style={{ color: 'var(--text-tertiary)', fontSize: 13 }}>Loading…</div>}

          {/* Confidence chart */}
          {chartData.length > 1 && (
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-tertiary)', marginBottom: 8 }}>
                Thesis evolution (confidence %)
              </div>
              <ResponsiveContainer width="100%" height={120}>
                <LineChart data={chartData}>
                  <XAxis dataKey="name" tick={{ fontSize: 9 }} interval="preserveStartEnd" />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 9 }} width={28} />
                  <Tooltip formatter={(v: any) => `${v}%`} />
                  <Line type="monotone" dataKey="confidence" stroke="#1565c0" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Run rows */}
          {history.length === 0 && !loading && (
            <div style={{ color: 'var(--text-tertiary)', fontSize: 13 }}>No runs found.</div>
          )}
          {history.map((row, i) => {
            const style = STANCE_STYLE[row.stance?.toUpperCase()] ?? STANCE_STYLE['UNKNOWN'];
            return (
              <div
                key={i}
                onClick={() => onSelectRun(row)}
                style={{
                  padding: '10px 12px', borderRadius: 8, marginBottom: 6,
                  background: 'var(--bg-secondary)', border: '0.5px solid var(--border)',
                  cursor: 'pointer', display: 'grid',
                  gridTemplateColumns: '1fr auto auto',
                  gap: '4px 12px', alignItems: 'center',
                }}
              >
                <div>
                  <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)' }}>{row.scenario}</span>
                  <span style={{ fontSize: 11, color: 'var(--text-tertiary)', marginLeft: 6 }}>{row.run_date?.slice(0, 10)}</span>
                </div>
                <span style={{
                  fontSize: 10, borderRadius: 4, padding: '1px 6px',
                  background: style.bg, color: style.color, fontWeight: 500,
                }}>{row.stance || 'UNKNOWN'}</span>
                <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>${(row.cost_usd ?? 0).toFixed(4)}</span>

                <div style={{ gridColumn: '1/-1', display: 'flex', gap: 12, fontSize: 11, color: 'var(--text-tertiary)' }}>
                  <span>⏱ {row.elapsed_seconds?.toFixed(1)}s</span>
                  <span>✓ {Math.round((row.completeness ?? 0))}% complete</span>
                  <span>conf {Math.round((row.confidence ?? 0) * 100)}%</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
};
