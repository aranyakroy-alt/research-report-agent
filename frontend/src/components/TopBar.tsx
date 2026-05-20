import React from 'react';

const SCENARIOS = ['S-A', 'S-B', 'S-C', 'S-D', 'S-E', 'S-F'];

interface TopBarProps {
  company: string;
  scenario: string;
  onCompanyChange: (v: string) => void;
  onScenarioChange: (v: string) => void;
  onRun: () => void;
  onHistory: () => void;
  running: boolean;
}

export const TopBar: React.FC<TopBarProps> = ({
  company, scenario, onCompanyChange, onScenarioChange,
  onRun, onHistory, running,
}) => (
  <div style={{
    height: 52, background: 'var(--bg-primary)',
    borderBottom: '0.5px solid var(--border)',
    display: 'flex', alignItems: 'center', gap: 12, padding: '0 16px',
    flexShrink: 0,
  }}>
    {/* Logo */}
    <span style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-primary)', marginRight: 4 }}>Research agent</span>
    <span style={{
      fontSize: 11, background: 'var(--info-bg)', color: 'var(--info-text)',
      borderRadius: 4, padding: '2px 8px',
    }}>V1</span>

    <div style={{ flex: 1 }} />

    {/* Company input */}
    <input
      type="text"
      value={company}
      onChange={e => onCompanyChange(e.target.value)}
      placeholder="Company name…"
      onKeyDown={e => { if (e.key === 'Enter' && !running) onRun(); }}
      style={{
        width: 200, height: 36, fontSize: 13,
        border: '0.5px solid var(--border-emphasis)',
        borderRadius: 6, padding: '0 10px',
        background: 'var(--bg-primary)', color: 'var(--text-primary)',
        outline: 'none',
      }}
    />

    {/* Scenario select */}
    <select
      value={scenario}
      onChange={e => onScenarioChange(e.target.value)}
      style={{
        height: 36, fontSize: 13,
        border: '0.5px solid var(--border-emphasis)',
        borderRadius: 6, padding: '0 8px',
        background: 'var(--bg-primary)', color: 'var(--text-primary)',
        outline: 'none',
      }}
    >
      {SCENARIOS.map(s => <option key={s} value={s}>{s}</option>)}
    </select>

    {/* Run button */}
    <button
      onClick={onRun}
      disabled={running || !company.trim()}
      style={{
        height: 36, padding: '0 16px', fontSize: 13, fontWeight: 500,
        borderRadius: 6, border: 'none', cursor: running ? 'not-allowed' : 'pointer',
        background: running ? 'var(--bg-tertiary)' : 'var(--text-primary)',
        color: running ? 'var(--text-tertiary)' : 'var(--bg-primary)',
      }}
    >
      {running ? 'Running…' : 'Run ↗'}
    </button>

    {/* History button */}
    <button
      onClick={onHistory}
      style={{
        height: 36, padding: '0 14px', fontSize: 13, fontWeight: 400,
        borderRadius: 6, border: '0.5px solid var(--border-emphasis)',
        cursor: 'pointer', background: 'none', color: 'var(--text-primary)',
      }}
    >
      History
    </button>
  </div>
);
