import React, { useState } from 'react';
import './index.css';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import History from './pages/History';
import { FaultQueryResponse } from './types';

type Page = 'home' | 'dashboard' | 'history';

function App() {
  const [page, setPage] = useState<Page>('home');
  const [selectedResult, setSelectedResult] = useState<FaultQueryResponse | null>(null);

  const handleSelectFromHistory = (result: FaultQueryResponse) => {
    setSelectedResult(result);
    setPage('home');
  };

  return (
    <div style={{ minHeight: '100vh' }}>
      <Navbar currentPage={page} onNavigate={setPage} />
      {page === 'home' && <Home />}
      {page === 'dashboard' && <Dashboard />}
      {page === 'history' && <History onSelectQuery={handleSelectFromHistory} />}
    </div>
  );
}

export default App;
