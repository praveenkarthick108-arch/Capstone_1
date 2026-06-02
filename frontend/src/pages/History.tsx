import React, { useState, useEffect } from 'react';
import { Clock, Search, Trash2, ChevronRight } from 'lucide-react';
import { FaultQueryResponse } from '../types';

const STORAGE_KEY = 'telecomiq_history';

export const saveToHistory = (result: FaultQueryResponse) => {
  try {
    const existing: FaultQueryResponse[] = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    const updated = [result, ...existing].slice(0, 20);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch {}
};

const severityColor: Record<string, string> = {
  HIGH: '#FF3B3B', MEDIUM: '#FF8C00', LOW: '#00C853',
};

const History: React.FC<{ onSelectQuery: (q: FaultQueryResponse) => void }> = ({ onSelectQuery }) => {
  const [history, setHistory] = useState<FaultQueryResponse[]>([]);

  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
      setHistory(stored);
    } catch {}
  }, []);

  const clearHistory = () => {
    localStorage.removeItem(STORAGE_KEY);
    setHistory([]);
  };

  if (history.length === 0) {
    return (
      <div style={{ maxWidth: 1400, margin: '0 auto', padding: '80px 24px', textAlign: 'center' }}>
        <Clock size={48} color="rgba(0,212,255,0.3)" style={{ marginBottom: 16 }} />
        <div style={{ fontSize: 18, fontWeight: 600, color: 'rgba(226,232,240,0.6)', marginBottom: 8 }}>No Query History</div>
        <div style={{ fontSize: 14, color: 'rgba(226,232,240,0.35)' }}>Run a fault analysis query to see it here</div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: '40px 24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: '#fff' }}>Query History</h2>
          <p style={{ margin: '4px 0 0', fontSize: 13, color: 'rgba(226,232,240,0.45)' }}>{history.length} recent queries</p>
        </div>
        <button
          onClick={clearHistory}
          style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 16px', borderRadius: 8, border: '1px solid rgba(255,59,59,0.3)', background: 'transparent', color: '#FF3B3B', cursor: 'pointer', fontSize: 13 }}
        >
          <Trash2 size={14} /> Clear All
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {history.map((item, i) => {
          const slaColor = severityColor[item.service_impact?.sla_breach_risk] || '#00C853';
          return (
            <div
              key={i}
              className="glass-card glass-hover"
              style={{ padding: '16px 20px', cursor: 'pointer', display: 'flex', gap: 16, alignItems: 'center' }}
              onClick={() => onSelectQuery(item)}
            >
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 8, flexWrap: 'wrap' }}>
                  <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.35)', fontFamily: 'monospace' }}>
                    {item.timestamp ? new Date(item.timestamp).toLocaleString() : ''}
                  </span>
                  <span style={{ fontSize: 10, padding: '1px 8px', borderRadius: 20, background: `${slaColor}18`, color: slaColor, border: `1px solid ${slaColor}40` }}>
                    {item.service_impact?.sla_breach_risk} SLA RISK
                  </span>
                  <span style={{ fontSize: 10, color: 'rgba(226,232,240,0.4)' }}>
                    {item.processing_time_ms ? `${(item.processing_time_ms / 1000).toFixed(1)}s` : ''}
                  </span>
                </div>
                <div style={{ fontSize: 14, color: '#fff', fontWeight: 500, marginBottom: 8, lineHeight: 1.4 }}>
                  {item.original_query}
                </div>
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                  {item.alarm_retrieval?.dominant_alarm_type && (
                    <span style={{ fontSize: 11, color: 'rgba(0,212,255,0.7)' }}>
                      🔔 {item.alarm_retrieval.dominant_alarm_type}
                    </span>
                  )}
                  {item.root_cause_analysis?.confidence_score !== undefined && (
                    <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.5)' }}>
                      Confidence: {Math.round(item.root_cause_analysis.confidence_score * 100)}%
                    </span>
                  )}
                  {item.service_impact?.affected_subscribers !== undefined && (
                    <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.5)' }}>
                      {item.service_impact.affected_subscribers.toLocaleString()} subscribers
                    </span>
                  )}
                </div>
              </div>
              <ChevronRight size={16} color="rgba(226,232,240,0.3)" />
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default History;
