import { useState, useRef } from 'react';
import { AgentEvent, RunResult } from '../types';

// CRA's dev proxy buffers SSE — connect directly to the backend for streaming.
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export function useAgentStream() {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [status, setStatus] = useState<'idle' | 'running' | 'complete' | 'error'>('idle');
  const [result, setResult] = useState<RunResult | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const startRun = async (company: string, scenario: string) => {
    // Close any existing stream
    if (esRef.current) { esRef.current.close(); esRef.current = null; }
    setEvents([]);
    setStatus('running');
    setResult(null);

    let jobId: string;
    try {
      const res = await fetch(`${API_BASE}/api/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company, scenario }),
      });
      const json = await res.json();
      jobId = json.job_id;
    } catch (e) {
      setStatus('error');
      return;
    }

    // Use direct backend URL — CRA proxy buffers SSE and blocks live events
    const es = new EventSource(`${API_BASE}/api/stream/${jobId}`);
    esRef.current = es;

    es.onmessage = (e) => {
      try {
        const event: AgentEvent = JSON.parse(e.data);
        if (event.type === 'complete') {
          setResult(event.data as RunResult);
          setStatus('complete');
          es.close();
        } else if (event.type === 'error') {
          setStatus('error');
          es.close();
        } else {
          setEvents((prev) => [...prev, event]);
        }
      } catch {}
    };

    es.onerror = () => {
      setStatus('error');
      es.close();
    };
  };

  return { events, status, result, startRun };
}
