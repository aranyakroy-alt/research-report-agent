import { useState, useCallback } from 'react';
import { HistoryRow } from '../types';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export function useHistory() {
  const [history, setHistory] = useState<HistoryRow[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchHistory = useCallback(async (company?: string) => {
    setLoading(true);
    try {
      const url = company
        ? `${API_BASE}/api/history/${encodeURIComponent(company)}`
        : `${API_BASE}/api/history`;
      const res = await fetch(url);
      const data = await res.json();
      setHistory(data);
    } catch {
      setHistory([]);
    } finally {
      setLoading(false);
    }
  }, []);

  return { history, loading, fetchHistory };
}
