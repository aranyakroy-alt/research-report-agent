import React from 'react';
import { DimStatus } from '../types';

interface DimensionGridProps {
  dims: Record<string, DimStatus>;
}

const STATUS_COLOR: Record<DimStatus, { bg: string; text: string }> = {
  pending: { bg: 'var(--bg-tertiary)', text: 'var(--text-tertiary)' },
  active:  { bg: 'var(--warn-bg)',    text: 'var(--warn-text)' },
  answered:{ bg: 'var(--ok-bg)',      text: 'var(--ok-text)' },
  failed:  { bg: 'var(--danger-bg)',  text: 'var(--danger-text)' },
};

export const DimensionGrid: React.FC<DimensionGridProps> = ({ dims }) => {
  // Sort all known dims: D1, D2, ... D9, D10, D11...
  const ids = Object.keys(dims).sort((a, b) => {
    const na = parseInt(a.replace('D', ''), 10);
    const nb = parseInt(b.replace('D', ''), 10);
    return na - nb;
  });

  // Always show at least D1-D6 as placeholders
  const base = ['D1','D2','D3','D4','D5','D6'];
  const allIds = Array.from(new Set([...base, ...ids])).sort((a, b) => {
    return parseInt(a.replace('D',''),10) - parseInt(b.replace('D',''),10);
  });

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 6 }}>
      {allIds.map(id => {
        const status: DimStatus = dims[id] ?? 'pending';
        const { bg, text } = STATUS_COLOR[status];
        const isGap = parseInt(id.replace('D',''),10) > 6;
        return (
          <div key={id} style={{
            background: bg, color: text,
            borderRadius: 6, padding: '6px 4px',
            textAlign: 'center', fontSize: 12, fontWeight: 500,
            outline: isGap ? '1.5px dashed var(--info-text)' : 'none',
          }}>
            {id}
            <div style={{ fontSize: 10, fontWeight: 400, marginTop: 2 }}>
              {isGap ? `gap` : status}
            </div>
          </div>
        );
      })}
    </div>
  );
};
