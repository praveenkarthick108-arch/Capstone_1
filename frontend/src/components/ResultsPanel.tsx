import React, { useState } from 'react';
import { FaultQueryResponse } from '../types';
import IncidentCard from './IncidentCard';
import {
  AlertTriangle, Shield, Zap, CheckCircle, Copy, ChevronDown, ChevronUp,
  Users, TrendingDown, Clock, Target, Link
} from 'lucide-react';

interface Props {
  result: FaultQueryResponse;
}

const PRIORITY_COLORS: Record<string, string> = {
  CRITICAL: '#FF3B3B',
  HIGH: '#FF8C00',
  MEDIUM: '#FFD700',
};

const SLA_RISK_COLORS: Record<string, { color: string; bg: string }> = {
  HIGH: { color: '#FF3B3B', bg: 'rgba(255,59,59,0.1)' },
  MEDIUM: { color: '#FF8C00', bg: 'rgba(255,140,0,0.1)' },
  LOW: { color: '#00C853', bg: 'rgba(0,200,83,0.1)' },
};

const ConfidenceGauge: React.FC<{ value: number }> = ({ value }) => {
  const pct = Math.round(value * 100);
  const color = pct >= 80 ? '#00C853' : pct >= 60 ? '#FFD700' : '#FF8C00';
  const circumference = 2 * Math.PI * 28;
  const dash = (pct / 100) * circumference;

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
      <svg width={72} height={72} viewBox="0 0 72 72">
        <circle cx={36} cy={36} r={28} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth={6} />
        <circle
          cx={36} cy={36} r={28} fill="none"
          stroke={color} strokeWidth={6}
          strokeDasharray={`${dash} ${circumference}`}
          strokeLinecap="round"
          transform="rotate(-90 36 36)"
          style={{ transition: 'stroke-dasharray 0.8s ease' }}
        />
        <text x={36} y={41} textAnchor="middle" fill={color} fontSize={16} fontWeight="bold">{pct}%</text>
      </svg>
      <div>
        <div style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>RCA Confidence</div>
        <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.5)' }}>
          {pct >= 80 ? 'High confidence' : pct >= 60 ? 'Moderate confidence' : 'Low confidence'}
        </div>
      </div>
    </div>
  );
};

const CopyButton: React.FC<{ text: string }> = ({ text }) => {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <button
      onClick={copy}
      style={{ background: 'none', border: 'none', cursor: 'pointer', color: copied ? '#00C853' : 'rgba(226,232,240,0.3)', padding: 4 }}
    >
      {copied ? <CheckCircle size={13} /> : <Copy size={13} />}
    </button>
  );
};

const Section: React.FC<{ title: string; icon: React.ReactNode; color?: string; children: React.ReactNode; defaultOpen?: boolean }> =
  ({ title, icon, color = '#00D4FF', children, defaultOpen = true }) => {
    const [open, setOpen] = useState(defaultOpen);
    return (
      <div className="glass-card" style={{ marginBottom: 16 }}>
        <div
          style={{ padding: '14px 18px', display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', borderBottom: open ? '1px solid rgba(0,212,255,0.08)' : 'none' }}
          onClick={() => setOpen(!open)}
        >
          <div style={{ color }}>{icon}</div>
          <span style={{ fontSize: 13, fontWeight: 600, color: '#fff', flex: 1 }}>{title}</span>
          {open ? <ChevronUp size={14} color="rgba(226,232,240,0.4)" /> : <ChevronDown size={14} color="rgba(226,232,240,0.4)" />}
        </div>
        {open && <div style={{ padding: '16px 18px' }} className="animate-fade-in">{children}</div>}
      </div>
    );
  };

const ResultsPanel: React.FC<Props> = ({ result }) => {
  const { alarm_retrieval, root_cause_analysis, service_impact, resolution_recommendations } = result;
  const slaStyle = SLA_RISK_COLORS[service_impact.sla_breach_risk] || SLA_RISK_COLORS.MEDIUM;

  return (
    <div className="animate-slide-up">
      {/* Header KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, marginBottom: 20 }}>
        <div className="glass-card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.45)', marginBottom: 6, letterSpacing: '0.5px' }}>SLA RISK</div>
          <div style={{ fontSize: 18, fontWeight: 700, color: slaStyle.color }}>{service_impact.sla_breach_risk}</div>
          <div style={{ fontSize: 10, color: 'rgba(226,232,240,0.35)' }}>Breach probability</div>
        </div>
        <div className="glass-card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.45)', marginBottom: 6, letterSpacing: '0.5px' }}>SUBSCRIBERS</div>
          <div style={{ fontSize: 18, fontWeight: 700, color: '#00D4FF' }}>{service_impact.affected_subscribers.toLocaleString()}</div>
          <div style={{ fontSize: 10, color: 'rgba(226,232,240,0.35)' }}>Affected users</div>
        </div>
        <div className="glass-card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.45)', marginBottom: 6, letterSpacing: '0.5px' }}>IMPACT SCORE</div>
          <div style={{ fontSize: 18, fontWeight: 700, color: '#F59E0B' }}>{service_impact.business_impact_score.toFixed(1)}/10</div>
          <div style={{ fontSize: 10, color: 'rgba(226,232,240,0.35)' }}>Business impact</div>
        </div>
        <div className="glass-card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.45)', marginBottom: 6, letterSpacing: '0.5px' }}>ETA TO RESOLVE</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: '#00FF88' }}>{resolution_recommendations.estimated_resolution_time}</div>
          <div style={{ fontSize: 10, color: 'rgba(226,232,240,0.35)' }}>Estimated time</div>
        </div>
        <div className="glass-card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.45)', marginBottom: 6, letterSpacing: '0.5px' }}>REVENUE IMPACT</div>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#FF8C00' }}>{service_impact.revenue_impact_estimate}</div>
          <div style={{ fontSize: 10, color: 'rgba(226,232,240,0.35)' }}>Estimated loss</div>
        </div>
        <div className="glass-card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.45)', marginBottom: 6, letterSpacing: '0.5px' }}>PROC. TIME</div>
          <div style={{ fontSize: 18, fontWeight: 700, color: 'rgba(226,232,240,0.7)' }}>{(result.processing_time_ms / 1000).toFixed(1)}s</div>
          <div style={{ fontSize: 10, color: 'rgba(226,232,240,0.35)' }}>Agent pipeline</div>
        </div>
      </div>

      {/* Root Cause Analysis */}
      <Section title="Root Cause Analysis" icon={<Brain16 />} color="#A855F7">
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 20, flexWrap: 'wrap' }}>
          <ConfidenceGauge value={root_cause_analysis.confidence_score} />
          <div style={{ flex: 1, minWidth: 200 }}>
            <div style={{ fontSize: 12, color: 'rgba(226,232,240,0.5)', marginBottom: 8 }}>FAULT CHAIN</div>
            <div style={{ fontSize: 13, color: 'rgba(226,232,240,0.85)', lineHeight: 1.6, padding: '10px 14px', background: 'rgba(168,85,247,0.06)', borderRadius: 8, borderLeft: '3px solid #A855F7' }}>
              {root_cause_analysis.root_cause_chain}
            </div>
          </div>
        </div>

        <div style={{ marginTop: 18 }}>
          <div style={{ fontSize: 12, color: 'rgba(226,232,240,0.5)', marginBottom: 10 }}>PROBABLE CAUSES</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {root_cause_analysis.probable_causes?.map((cause, i) => (
              <div key={i} style={{ display: 'flex', gap: 12, alignItems: 'flex-start', padding: '10px 14px', background: 'rgba(255,255,255,0.02)', borderRadius: 8, border: '1px solid rgba(255,255,255,0.06)' }}>
                <div style={{ minWidth: 40, fontSize: 12, fontWeight: 600, color: cause.confidence >= 0.7 ? '#00C853' : cause.confidence >= 0.5 ? '#FFD700' : '#FF8C00' }}>
                  {Math.round(cause.confidence * 100)}%
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, color: '#fff', marginBottom: 4 }}>{cause.cause}</div>
                  <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.45)' }}>{cause.evidence}</div>
                </div>
                <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 20, background: 'rgba(255,255,255,0.05)', color: 'rgba(226,232,240,0.5)', border: '1px solid rgba(255,255,255,0.08)', whiteSpace: 'nowrap' }}>
                  {cause.category}
                </span>
              </div>
            ))}
          </div>
        </div>

        {root_cause_analysis.technical_explanation && (
          <div style={{ marginTop: 16, padding: '12px 14px', background: 'rgba(168,85,247,0.05)', borderRadius: 8, borderLeft: '2px solid rgba(168,85,247,0.4)' }}>
            <div style={{ fontSize: 11, color: 'rgba(168,85,247,0.8)', marginBottom: 6, fontWeight: 600 }}>TECHNICAL EXPLANATION</div>
            <p style={{ margin: 0, fontSize: 13, color: 'rgba(226,232,240,0.7)', lineHeight: 1.7 }}>
              {root_cause_analysis.technical_explanation}
            </p>
          </div>
        )}
      </Section>

      {/* Resolution Steps */}
      <Section title="Troubleshooting Playbook" icon={<WrenchIcon />} color="#00FF88">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {resolution_recommendations.immediate_steps?.map((step, i) => (
            <div key={i} style={{ display: 'flex', gap: 14, padding: '12px 14px', background: 'rgba(0,255,136,0.03)', borderRadius: 8, border: '1px solid rgba(0,255,136,0.08)' }}>
              <div style={{ minWidth: 28, height: 28, borderRadius: '50%', background: 'rgba(0,255,136,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700, color: '#00FF88', flexShrink: 0 }}>
                {step.step}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                  <span style={{ fontSize: 13, fontWeight: 500, color: '#fff' }}>{step.action}</span>
                  <span style={{ fontSize: 10, padding: '1px 7px', borderRadius: 20, fontWeight: 600, background: PRIORITY_COLORS[step.priority] ? `${PRIORITY_COLORS[step.priority]}18` : 'rgba(255,255,255,0.05)', color: PRIORITY_COLORS[step.priority] || 'rgba(226,232,240,0.5)', border: `1px solid ${PRIORITY_COLORS[step.priority] ? PRIORITY_COLORS[step.priority] + '40' : 'rgba(255,255,255,0.08)'}` }}>
                    {step.priority}
                  </span>
                </div>
                {step.command && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <code style={{ fontSize: 11, fontFamily: 'JetBrains Mono, monospace', padding: '3px 10px', background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(0,212,255,0.15)', borderRadius: 6, color: '#00D4FF', flex: 1 }}>
                      {step.command}
                    </code>
                    <CopyButton text={step.command} />
                  </div>
                )}
                {step.expected_outcome && (
                  <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.45)' }}>→ {step.expected_outcome}</div>
                )}
              </div>
            </div>
          ))}
        </div>

        {resolution_recommendations.vendor_specific_commands?.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 12, color: 'rgba(226,232,240,0.5)', marginBottom: 10 }}>VENDOR-SPECIFIC COMMANDS</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {resolution_recommendations.vendor_specific_commands.slice(0, 5).map((cmd, i) => (
                <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'center', padding: '8px 12px', background: 'rgba(0,0,0,0.2)', borderRadius: 6 }}>
                  <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 20, background: 'rgba(0,212,255,0.1)', color: '#00D4FF', border: '1px solid rgba(0,212,255,0.2)', whiteSpace: 'nowrap', minWidth: 60, textAlign: 'center' }}>
                    {cmd.vendor}
                  </span>
                  <code style={{ flex: 1, fontSize: 11, fontFamily: 'monospace', color: '#00FF88' }}>{cmd.command}</code>
                  <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.4)', minWidth: 120 }}>{cmd.purpose}</span>
                  <CopyButton text={cmd.command} />
                </div>
              ))}
            </div>
          </div>
        )}

        <div style={{ marginTop: 16, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <div style={{ padding: '12px 14px', background: 'rgba(255,140,0,0.05)', borderRadius: 8, border: '1px solid rgba(255,140,0,0.15)' }}>
            <div style={{ fontSize: 11, color: '#FF8C00', marginBottom: 6, fontWeight: 600 }}>ESCALATION PATH</div>
            <p style={{ margin: 0, fontSize: 12, color: 'rgba(226,232,240,0.7)', lineHeight: 1.5 }}>{resolution_recommendations.escalation_path}</p>
          </div>
          <div style={{ padding: '12px 14px', background: 'rgba(0,212,255,0.05)', borderRadius: 8, border: '1px solid rgba(0,212,255,0.12)' }}>
            <div style={{ fontSize: 11, color: '#00D4FF', marginBottom: 6, fontWeight: 600 }}>PREVENTION MEASURES</div>
            <ul style={{ margin: 0, padding: '0 0 0 16px', listStyle: 'disc' }}>
              {resolution_recommendations.prevention_measures?.slice(0, 3).map((m, i) => (
                <li key={i} style={{ fontSize: 12, color: 'rgba(226,232,240,0.65)', marginBottom: 4, lineHeight: 1.5 }}>{m}</li>
              ))}
            </ul>
          </div>
        </div>
      </Section>

      {/* Service Impact */}
      <Section title="Service Impact Assessment" icon={<TrendingDown size={16} />} color="#F59E0B" defaultOpen={false}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12, marginBottom: 14 }}>
          <div>
            <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.45)', marginBottom: 4 }}>IMPACTED SERVICES</div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {service_impact.impacted_services?.map((s, i) => (
                <span key={i} style={{ fontSize: 11, padding: '2px 8px', borderRadius: 20, background: 'rgba(245,158,11,0.1)', color: '#F59E0B', border: '1px solid rgba(245,158,11,0.25)' }}>{s}</span>
              ))}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.45)', marginBottom: 4 }}>AFFECTED REGIONS</div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {service_impact.affected_regions?.map((r, i) => (
                <span key={i} style={{ fontSize: 11, padding: '2px 8px', borderRadius: 20, background: 'rgba(0,212,255,0.08)', color: '#00D4FF', border: '1px solid rgba(0,212,255,0.2)' }}>{r}</span>
              ))}
            </div>
          </div>
        </div>
      </Section>

      {/* Retrieved Incidents */}
      <Section title={`Similar Incidents (${alarm_retrieval.retrieved_incidents.length})`} icon={<Search16 />} color="#00D4FF" defaultOpen={false}>
        <div style={{ marginBottom: 10, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.5)' }}>
            Dominant: <strong style={{ color: '#00D4FF' }}>{alarm_retrieval.dominant_alarm_type}</strong>
          </span>
          {alarm_retrieval.alarm_patterns?.slice(0, 3).map((p, i) => (
            <span key={i} style={{ fontSize: 11, padding: '1px 8px', borderRadius: 20, background: 'rgba(0,212,255,0.08)', color: 'rgba(0,212,255,0.7)', border: '1px solid rgba(0,212,255,0.15)' }}>
              {p}
            </span>
          ))}
        </div>
        {alarm_retrieval.retrieved_incidents.map((inc, i) => (
          <IncidentCard key={inc.alarm_id} incident={inc} rank={i + 1} />
        ))}
      </Section>
    </div>
  );
};

// Tiny icon wrappers to avoid import issues in JSX
const Brain16 = () => (
  <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M9.5 2C8.8 2 8 2.7 8 3.5v1C8 5.3 7.3 6 6.5 6c-.8 0-1.5.7-1.5 1.5S5.7 9 6.5 9c.8 0 1.5.7 1.5 1.5S7.3 12 6.5 12h-1C4.7 12 4 12.7 4 13.5S4.7 15 5.5 15c.8 0 1.5.7 1.5 1.5S6.3 18 5.5 18H5c-.6 0-1 .4-1 1s.4 1 1 1h14c.6 0 1-.4 1-1s-.4-1-1-1h-.5c-.8 0-1.5-.7-1.5-1.5s.7-1.5 1.5-1.5c.8 0 1.5-.7 1.5-1.5s-.7-1.5-1.5-1.5h-1c-.8 0-1.5-.7-1.5-1.5s.7-1.5 1.5-1.5c.8 0 1.5-.7 1.5-1.5S19.3 6 18.5 6c-.8 0-1.5-.7-1.5-1.5v-1C17 2.7 16.2 2 15.5 2h-6z"/>
  </svg>
);
const WrenchIcon = () => (
  <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
  </svg>
);
const Search16 = () => (
  <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <circle cx={11} cy={11} r={8}/><line x1={21} y1={21} x2={16.65} y2={16.65}/>
  </svg>
);

export default ResultsPanel;
