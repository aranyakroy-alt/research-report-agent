import React from 'react';

interface VerdictBarProps {
  stance: string;
  confidence: number; // 0-1
}

const STANCE_STYLE: Record<string, { bg: string; text: string }> = {
  BUY:        { bg: 'var(--ok-bg)',      text: 'var(--ok-text)' },
  HOLD:       { bg: 'var(--warn-bg)',    text: 'var(--warn-text)' },
  AVOID:      { bg: 'var(--danger-bg)',  text: 'var(--danger-text)' },
  SUPPORTS:   { bg: 'var(--ok-bg)',      text: 'var(--ok-text)' },
  CONTRADICTS:{ bg: 'var(--danger-bg)',  text: 'var(--danger-text)' },
  NEUTRAL:    { bg: 'var(--info-bg)',    text: 'var(--info-text)' },
  UNKNOWN:    { bg: 'var(--bg-tertiary)',text: 'var(--text-tertiary)' },
};

export const VerdictBar: React.FC<VerdictBarProps> = ({ stance, confidence }) => {
  const style = STANCE_STYLE[stance.toUpperCase()] ?? STANCE_STYLE['UNKNOWN'];
  const pct = Math.round(confidence * 100);
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <span style={{
        background: style.bg, color: style.text,
        borderRadius: 4, padding: '3px 10px', fontSize: 12, fontWeight: 500,
        whiteSpace: 'nowrap',
      }}>{stance || 'UNKNOWN'}</span>
      <div style={{ flex: 1, height: 6, background: 'var(--bg-tertiary)', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{
          width: `${pct}%`, height: '100%',
          background: style.text, borderRadius: 3, transition: 'width 0.5s',
        }} />
      </div>
      <span style={{ fontSize: 12, color: 'var(--text-secondary)', minWidth: 36, textAlign: 'right' }}>{pct}%</span>
    </div>
  );
};
