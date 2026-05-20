import React, { useState } from 'react';
import { TopBar } from './components/TopBar';
import { AgentTrace } from './components/AgentTrace';
import { ResultsPanel } from './components/ResultsPanel';
import { HistoryDrawer } from './components/HistoryDrawer';
import { useAgentStream } from './hooks/useAgentStream';
import { HistoryRow } from './types';
import './App.css';

function App() {
  const [company, setCompany] = useState('Reliance Industries');
  const [scenario, setScenario] = useState('S-A');
  const [historyOpen, setHistoryOpen] = useState(false);
  const { events, status, result, startRun } = useAgentStream();

  const handleRun = () => {
    if (!company.trim() || status === 'running') return;
    startRun(company.trim(), scenario);
  };

  const handleSelectRun = (row: HistoryRow) => {
    setCompany(row.company);
    setScenario(row.scenario);
    setHistoryOpen(false);
  };

  return (
    <div className="app-root">
      <TopBar
        company={company}
        scenario={scenario}
        onCompanyChange={setCompany}
        onScenarioChange={setScenario}
        onRun={handleRun}
        onHistory={() => setHistoryOpen(o => !o)}
        running={status === 'running'}
      />
      <div className="panels">
        <div className="panel panel-left">
          <AgentTrace events={events} status={status} />
        </div>
        <div className="panel panel-right">
          <ResultsPanel result={result} events={events} scenario={scenario} />
        </div>
      </div>
      <HistoryDrawer
        company={company}
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        onSelectRun={handleSelectRun}
      />
    </div>
  );
}

export default App;
