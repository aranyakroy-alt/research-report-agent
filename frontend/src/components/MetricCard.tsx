import React from 'react';

interface MetricCardProps {
  label: string;
  value: string;
  sub?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({ label, value, sub }) => (
  <div style={{
    background: 'var(--bg-secondary)',
    border: '0.5px solid var(--border)',
    borderRadius: 8,
    padding: '10px 14px',
    flex: 1,
    minWidth: 0,
  }}>
    <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-tertiary)', marginBottom: 4 }}>
      {label}
    </div>
    <div style={{ fontSize: 22, fontWeight: 500, color: 'var(--text-primary)' }}>{value}</div>
    {sub && <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>{sub}</div>}
  </div>
);
