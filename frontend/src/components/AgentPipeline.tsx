import React from 'react';
import { AgentStatus } from '../types';
import { Search, Brain, TrendingUp, Wrench, CheckCircle, Loader, AlertCircle, Clock } from 'lucide-react';

interface Props {
  statuses: AgentStatus[];
  isRunning: boolean;
}

const AGENT_ICONS = [
  <Search size={18} />,
  <Brain size={18} />,
  <TrendingUp size={18} />,
  <Wrench size={18} />,
];

const AGENT_COLORS = ['#00D4FF', '#A855F7', '#F59E0B', '#00FF88'];

const AGENT_LABELS = [
  'Alarm Retrieval',
  'Root Cause Analysis',
  'Service Impact',
  'Resolution Planner',
];

const AgentPipeline: React.FC<Props> = ({ statuses, isRunning }) => {
  const agents = AGENT_LABELS.map((label, i) => {
    const s = statuses[i];
    return {
      label,
      icon: AGENT_ICONS[i],
      color: AGENT_COLORS[i],
      status: s?.status || (isRunning && i === 0 ? 'running' : 'pending'),
      duration_ms: s?.duration_ms,
    };
  });

  return (
    <div style={{ padding: '20px 0' }}>
      <div style={{ fontSize: 12, color: 'rgba(0,212,255,0.7)', letterSpacing: '1.5px', textTransform: 'uppercase', marginBottom: 16 }}>
        Multi-Agent Pipeline
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 0 }}>
        {agents.map((agent, i) => (
          <React.Fragment key={i}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  borderRadius: 10,
                  border: `1px solid ${agent.status === 'completed' ? agent.color + '60' : agent.status === 'running' ? agent.color : 'rgba(255,255,255,0.08)'}`,
                  background: agent.status === 'completed'
                    ? `${agent.color}10`
                    : agent.status === 'running'
                    ? `${agent.color}18`
                    : 'rgba(255,255,255,0.02)',
                  padding: '12px 14px',
                  transition: 'all 0.3s',
                  boxShadow: agent.status === 'running' ? `0 0 16px ${agent.color}30` : 'none',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <div style={{ color: agent.status === 'pending' ? 'rgba(255,255,255,0.3)' : agent.color }}>
                    {agent.icon}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: agent.status === 'pending' ? 'rgba(255,255,255,0.3)' : '#fff' }}>
                      {agent.label}
                    </div>
                  </div>
                  <div>
                    {agent.status === 'completed' && <CheckCircle size={14} color={agent.color} />}
                    {agent.status === 'running' && (
                      <div style={{ animation: 'spin 1s linear infinite', display: 'flex' }}>
                        <Loader size={14} color={agent.color} />
                      </div>
                    )}
                    {agent.status === 'pending' && <Clock size={14} color="rgba(255,255,255,0.2)" />}
                    {agent.status === 'failed' && <AlertCircle size={14} color="#FF3B3B" />}
                  </div>
                </div>
                {agent.duration_ms !== undefined && (
                  <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.35)', fontFamily: 'monospace' }}>
                    {agent.duration_ms}ms
                  </div>
                )}
                {agent.status === 'running' && (
                  <div style={{ marginTop: 6 }}>
                    <div style={{ height: 2, background: 'rgba(255,255,255,0.05)', borderRadius: 2, overflow: 'hidden' }}>
                      <div
                        style={{
                          height: '100%', width: '60%', background: agent.color,
                          borderRadius: 2,
                          animation: 'progress 1.5s ease-in-out infinite',
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
            {i < agents.length - 1 && (
              <div style={{ width: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <div
                  style={{
                    width: '100%', height: 2,
                    background: agents[i].status === 'completed'
                      ? `linear-gradient(90deg, ${agents[i].color}, ${agents[i + 1].color})`
                      : 'rgba(255,255,255,0.07)',
                    transition: 'background 0.3s',
                  }}
                />
              </div>
            )}
          </React.Fragment>
        ))}
      </div>
      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes progress { 0% { transform: translateX(-100%); } 100% { transform: translateX(250%); } }
      `}</style>
    </div>
  );
};

export default AgentPipeline;
