import React, { useState, useEffect, useRef } from 'react';
import { FaultQueryResponse, QueryFilters } from '../types';
import { queryFault } from '../services/api';
import FilterPanel from '../components/FilterPanel';
import AgentPipeline from '../components/AgentPipeline';
import ResultsPanel from '../components/ResultsPanel';
import { Search, Zap, AlertCircle } from 'lucide-react';

const EXAMPLE_QUERIES = [
  "5G gNB sites in North region showing X2 interface failures...",
  "Multiple eNodeBs reporting S1 interface failure after maintenance...",
  "Fiber cut causing high latency between backbone nodes...",
  "MPLS LDP session flap causing traffic blackhole...",
  "PTP synchronization failure affecting 5G TDD sites...",
  "BTS towers reporting GNSS antenna failures in East region...",
];

const Home: React.FC = () => {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<QueryFilters>({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FaultQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [placeholderIdx, setPlaceholderIdx] = useState(0);
  const [showFilters, setShowFilters] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const interval = setInterval(() => setPlaceholderIdx((i) => (i + 1) % EXAMPLE_QUERIES.length), 3500);
    return () => clearInterval(interval);
  }, []);

  const handleQuery = async () => {
    if (!query.trim() || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await queryFault(query.trim(), filters);
      setResult(data);
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message || 'Analysis failed. Please check the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleQuery();
  };

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: '40px 24px' }}>
      {/* Hero */}
      <div style={{ textAlign: 'center', marginBottom: 40 }}>
        <div
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 8, marginBottom: 16,
            padding: '6px 16px', borderRadius: 20,
            background: 'rgba(0,212,255,0.08)', border: '1px solid rgba(0,212,255,0.2)',
          }}
        >
          <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#00FF88', boxShadow: '0 0 6px #00FF88' }} />
          <span style={{ fontSize: 12, color: 'rgba(0,212,255,0.8)', letterSpacing: '1px' }}>
            AI-POWERED FAULT INTELLIGENCE
          </span>
        </div>
        <h1 style={{ fontSize: 'clamp(28px, 4vw, 48px)', fontWeight: 800, margin: '0 0 12px', letterSpacing: '-1px', color: '#fff', lineHeight: 1.1 }}>
          Telecom Network{' '}
          <span style={{ background: 'linear-gradient(135deg, #00D4FF, #0066CC)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Fault Intelligence
          </span>
        </h1>
        <p style={{ fontSize: 16, color: 'rgba(226,232,240,0.55)', margin: 0 }}>
          Describe any network issue in natural language — AI agents retrieve, correlate, and diagnose in seconds
        </p>
      </div>

      {/* Search box */}
      <div className="glass-card" style={{ padding: 20, marginBottom: 16 }}>
        <textarea
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={EXAMPLE_QUERIES[placeholderIdx]}
          rows={3}
          style={{
            width: '100%', background: 'transparent', border: 'none', outline: 'none',
            color: '#fff', fontSize: 15, resize: 'none', fontFamily: 'Inter, sans-serif',
            lineHeight: 1.6,
          }}
        />
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 12 }}>
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              onClick={() => setShowFilters(!showFilters)}
              style={{
                padding: '7px 14px', borderRadius: 8, fontSize: 12,
                border: `1px solid ${showFilters ? 'rgba(0,212,255,0.4)' : 'rgba(255,255,255,0.1)'}`,
                background: showFilters ? 'rgba(0,212,255,0.08)' : 'transparent',
                color: showFilters ? '#00D4FF' : 'rgba(226,232,240,0.5)',
                cursor: 'pointer',
              }}
            >
              {showFilters ? 'Hide Filters' : 'Add Filters'}
            </button>
            <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.3)', alignSelf: 'center' }}>Ctrl+Enter to run</span>
          </div>
          <button
            onClick={handleQuery}
            disabled={loading || !query.trim()}
            style={{
              display: 'flex', alignItems: 'center', gap: 8, padding: '10px 24px',
              borderRadius: 10, border: 'none', cursor: loading || !query.trim() ? 'not-allowed' : 'pointer',
              background: loading || !query.trim()
                ? 'rgba(0,212,255,0.15)'
                : 'linear-gradient(135deg, #00D4FF, #0066CC)',
              color: '#fff', fontWeight: 600, fontSize: 14, transition: 'all 0.2s',
              boxShadow: loading || !query.trim() ? 'none' : '0 0 20px rgba(0,212,255,0.3)',
            }}
          >
            {loading ? (
              <>
                <div style={{ width: 16, height: 16, border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
                Analyzing...
              </>
            ) : (
              <>
                <Zap size={16} />
                Analyze Fault
              </>
            )}
          </button>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="glass-card animate-fade-in" style={{ padding: '16px 20px', marginBottom: 16 }}>
          <FilterPanel filters={filters} onChange={setFilters} />
        </div>
      )}

      {/* Agent pipeline (loading state) */}
      {loading && (
        <div className="glass-card animate-fade-in" style={{ padding: '16px 20px', marginBottom: 20 }}>
          <AgentPipeline statuses={[]} isRunning={true} />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="glass-card animate-fade-in" style={{ padding: 16, marginBottom: 16, borderColor: 'rgba(255,59,59,0.3)', background: 'rgba(255,59,59,0.05)' }}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
            <AlertCircle size={16} color="#FF3B3B" style={{ flexShrink: 0, marginTop: 2 }} />
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#FF3B3B', marginBottom: 4 }}>Analysis Failed</div>
              <div style={{ fontSize: 13, color: 'rgba(226,232,240,0.7)' }}>{error}</div>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <>
          <div className="glass-card animate-fade-in" style={{ padding: '16px 20px', marginBottom: 20 }}>
            <AgentPipeline statuses={result.agent_statuses} isRunning={false} />
          </div>
          <ResultsPanel result={result} />
        </>
      )}

      {/* Empty state */}
      {!result && !loading && !error && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12, marginTop: 20 }}>
          {['5G gNB X2 interface failures after firmware upgrade in North region',
            'Multiple eNodeBs S1 failure BGP route error on backhaul',
            'Fiber backbone latency spike between hub nodes DWDM OSNR degraded',
            'PTP grandmaster clock failure 5G NR TDD sync loss East region'].map((q, i) => (
            <button
              key={i}
              onClick={() => setQuery(q)}
              className="glass-card glass-hover"
              style={{
                padding: '14px 16px', textAlign: 'left', cursor: 'pointer',
                border: '1px solid rgba(0,212,255,0.08)', background: 'rgba(255,255,255,0.02)',
                color: 'inherit', transition: 'all 0.2s',
              }}
            >
              <div style={{ fontSize: 10, color: 'rgba(0,212,255,0.6)', marginBottom: 6, letterSpacing: '0.5px' }}>TRY EXAMPLE</div>
              <div style={{ fontSize: 13, color: 'rgba(226,232,240,0.7)', lineHeight: 1.5 }}>{q}</div>
            </button>
          ))}
        </div>
      )}

      <style>{`@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }`}</style>
    </div>
  );
};

export default Home;
