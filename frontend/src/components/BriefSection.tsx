import React, { useState } from 'react';

interface BriefSectionProps {
  title: string;
  content: string;
}

export const BriefSection: React.FC<BriefSectionProps> = ({ title, content }) => {
  const [open, setOpen] = useState(false);
  return (
    <div style={{ borderBottom: '0.5px solid var(--border)' }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          width: '100%', background: 'none', border: 'none', cursor: 'pointer',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '8px 0', textAlign: 'left',
          fontSize: 13, fontWeight: 500, color: 'var(--text-primary)',
        }}
      >
        {title}
        <span style={{ color: 'var(--text-tertiary)', fontSize: 11 }}>{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div style={{
          fontSize: 13, lineHeight: 1.6, color: 'var(--text-secondary)',
          paddingBottom: 10, whiteSpace: 'pre-wrap',
        }}>
          {content}
        </div>
      )}
    </div>
  );
};
