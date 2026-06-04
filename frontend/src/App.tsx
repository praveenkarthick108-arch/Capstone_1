import React, { useState } from 'react';
import './index.css';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import History from './pages/History';
import Architecture from './pages/Architecture';
import { FaultQueryResponse } from './types';

type Page = 'home' | 'dashboard' | 'history' | 'architecture';

function App() {
  const [page, setPage] = useState<Page>('home');
  const [restoredResult, setRestoredResult] = useState<FaultQueryResponse | null>(null);

  const handleSelectFromHistory = (result: FaultQueryResponse) => {
    setRestoredResult(result);
    setPage('home');
  };

  return (
    <div style={{ minHeight: '100vh' }}>
      <Navbar currentPage={page} onNavigate={setPage} />
      {/* Keep Home mounted at all times — hide with CSS so state is preserved on navigation */}
      <div style={{ display: page === 'home' ? 'block' : 'none' }}>
        <Home restoredResult={restoredResult} onResultRestored={() => setRestoredResult(null)} />
      </div>
      {page === 'dashboard' && <Dashboard />}
      {page === 'history' && <History onSelectQuery={handleSelectFromHistory} />}
      {page === 'architecture' && <Architecture />}
    </div>
  );
}

export default App;
