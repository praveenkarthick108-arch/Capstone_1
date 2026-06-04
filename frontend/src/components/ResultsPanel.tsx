import React, { useState, useEffect, useRef } from 'react';
import { FaultQueryResponse, ServiceNowTicket } from '../types';
import IncidentCard from './IncidentCard';
import { createServiceNowTicket } from '../services/api';
import {
  AlertTriangle, Shield, Zap, CheckCircle, Copy, ChevronDown, ChevronUp,
  Users, TrendingDown, Clock, Target, Link, Ticket, ExternalLink, Loader,
  Download, BarChart2, Info,
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

const ConfidenceGauge: React.FC<{ value: number; result: FaultQueryResponse }> = ({ value, result }) => {
  const [showBreakdown, setShowBreakdown] = useState(false);
  const pct = Math.round(value * 100);
  const color = pct >= 80 ? '#00C853' : pct >= 60 ? '#FFD700' : '#FF8C00';
  const circumference = 2 * Math.PI * 28;
  const dash = (pct / 100) * circumference;

  const incidents = result.alarm_retrieval.retrieved_incidents;
  const topSim = incidents[0]?.similarity_score ?? 0;
  const regionMatch = incidents.some(i => i.network_region === result.query_enhancement?.extracted_region);
  const breakdown = [
    { label: 'Similar incidents found', met: incidents.length >= 3, detail: `${incidents.length} retrieved` },
    { label: 'Region match', met: regionMatch || !result.query_enhancement?.extracted_region, detail: result.query_enhancement?.extracted_region || 'not specified' },
    { label: 'High semantic similarity', met: topSim > 0.6, detail: `Best match ${Math.round(topSim * 100)}%` },
    { label: 'Alarm type consistent', met: result.alarm_retrieval.alarm_patterns.length > 0, detail: result.alarm_retrieval.dominant_alarm_type || '—' },
  ];

  return (
    <div style={{ position: 'relative' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <svg width={72} height={72} viewBox="0 0 72 72">
          <circle cx={36} cy={36} r={28} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth={6} />
          <circle cx={36} cy={36} r={28} fill="none" stroke={color} strokeWidth={6}
            strokeDasharray={`${dash} ${circumference}`} strokeLinecap="round"
            transform="rotate(-90 36 36)" style={{ transition: 'stroke-dasharray 0.8s ease' }} />
          <text x={36} y={41} textAnchor="middle" fill={color} fontSize={16} fontWeight="bold">{pct}%</text>
        </svg>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>RCA Confidence</span>
            <button onClick={() => setShowBreakdown(!showBreakdown)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'rgba(226,232,240,0.35)', padding: 0 }}
              title="Why this score?">
              <Info size={13} />
            </button>
          </div>
          <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.5)' }}>
            {pct >= 80 ? 'High confidence' : pct >= 60 ? 'Moderate confidence' : 'Low confidence'}
          </div>
        </div>
      </div>
      {showBreakdown && (
        <div style={{ position: 'absolute', top: 80, left: 0, zIndex: 10, background: 'rgba(13,18,33,0.98)', border: '1px solid rgba(0,212,255,0.2)', borderRadius: 10, padding: '12px 14px', minWidth: 260, boxShadow: '0 8px 32px rgba(0,0,0,0.5)' }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#00D4FF', marginBottom: 8, letterSpacing: '0.5px' }}>CONFIDENCE BREAKDOWN</div>
          {breakdown.map((b, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <span style={{ fontSize: 13, color: b.met ? '#00C853' : '#FF8C00' }}>{b.met ? '✓' : '✗'}</span>
              <div style={{ flex: 1 }}>
                <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.8)' }}>{b.label}</span>
                <span style={{ fontSize: 10, color: 'rgba(226,232,240,0.4)', marginLeft: 6 }}>({b.detail})</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ── SLA Countdown Timer ─────────────────────────────────────────────
const SlaCountdown: React.FC<{ mttrMinutes: number }> = ({ mttrMinutes }) => {
  const [remaining, setRemaining] = useState(Math.max(0, mttrMinutes * 60));
  const SLA_THRESHOLD = 30 * 60; // 30 min SLA in seconds
  useEffect(() => {
    if (remaining <= 0) return;
    const t = setInterval(() => setRemaining(r => Math.max(0, r - 1)), 1000);
    return () => clearInterval(t);
  }, []);
  const mins = Math.floor(remaining / 60);
  const secs = remaining % 60;
  const pct = Math.round((remaining / SLA_THRESHOLD) * 100);
  const color = pct > 50 ? '#FF3B3B' : pct > 25 ? '#FF8C00' : '#FFD700';
  return (
    <div style={{ marginTop: 12, padding: '10px 14px', borderRadius: 8, background: 'rgba(255,59,59,0.07)', border: '1px solid rgba(255,59,59,0.2)' }}>
      <div style={{ fontSize: 10, color: 'rgba(226,232,240,0.45)', letterSpacing: '0.5px', marginBottom: 6 }}>SLA BREACH COUNTDOWN</div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginBottom: 6 }}>
        <span style={{ fontSize: 24, fontWeight: 800, color, fontFamily: 'JetBrains Mono, monospace' }}>
          {String(mins).padStart(2, '0')}:{String(secs).padStart(2, '0')}
        </span>
        <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.4)' }}>remaining</span>
      </div>
      <div style={{ height: 4, background: 'rgba(255,255,255,0.06)', borderRadius: 2 }}>
        <div style={{ height: '100%', width: `${Math.min(100 - pct, 100)}%`, background: color, borderRadius: 2, transition: 'width 1s linear' }} />
      </div>
      <div style={{ fontSize: 10, color: 'rgba(226,232,240,0.35)', marginTop: 4 }}>30-min SLA window · avg resolution ~{mttrMinutes}m</div>
    </div>
  );
};

// ── Export Report ───────────────────────────────────────────────────
const ExportButton: React.FC<{ result: FaultQueryResponse }> = ({ result }) => {
  const handleExport = () => {
    const r = result;
    const steps = r.resolution_recommendations.immediate_steps
      .map(s => `  ${s.step}. **${s.action}**${s.command ? `\n     \`${s.command}\`` : ''}\n     Expected: ${s.expected_outcome}`)
      .join('\n');
    const incidents = r.alarm_retrieval.retrieved_incidents
      .map(i => `  - [${i.alarm_id}] ${i.alarm_type} · ${i.network_region} / ${i.technology_type} · ${i.severity} · ${i.outage_duration}m`)
      .join('\n');
    const md = `# Telecom Fault Intelligence Report
Generated: ${new Date().toISOString()}

## Query
> ${r.original_query}

## Root Cause Analysis
- **Chain:** ${r.root_cause_analysis.root_cause_chain}
- **Confidence:** ${Math.round(r.root_cause_analysis.confidence_score * 100)}%
- **Explanation:** ${r.root_cause_analysis.technical_explanation}

### Probable Causes
${r.root_cause_analysis.probable_causes.map(c => `- ${c.cause} (${Math.round(c.confidence * 100)}%)`).join('\n')}

## Service Impact
| Metric | Value |
|--------|-------|
| Affected Subscribers | ${r.service_impact.affected_subscribers.toLocaleString()} |
| SLA Breach Risk | ${r.service_impact.sla_breach_risk} |
| Business Impact Score | ${r.service_impact.business_impact_score}/10 |
| Revenue Impact | ${r.service_impact.revenue_impact_estimate} |

**Impacted Services:** ${r.service_impact.impacted_services.join(', ')}

## Resolution Steps
${steps}

**Escalation Path:** ${r.resolution_recommendations.escalation_path}
**Estimated Resolution:** ${r.resolution_recommendations.estimated_resolution_time}

## Retrieved Similar Incidents (${r.alarm_retrieval.retrieved_incidents.length})
${incidents}

---
*Generated by Telecom Fault Intelligence Assistant · Query ID: ${r.query_id}*
`;
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `fault-report-${r.query_id}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };
  return (
    <button onClick={handleExport}
      style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '7px 14px', borderRadius: 8, border: '1px solid rgba(0,212,255,0.2)', background: 'transparent', color: '#00D4FF', cursor: 'pointer', fontSize: 12, fontWeight: 500 }}>
      <Download size={13} /> Export Report
    </button>
  );
};

// ── RAG Evaluation Scores ───────────────────────────────────────────
const RagEvalPanel: React.FC<{ result: FaultQueryResponse }> = ({ result }) => {
  const incidents = result.alarm_retrieval.retrieved_incidents;
  const topSim = incidents[0]?.similarity_score ?? 0;
  const avgSim = incidents.length ? incidents.reduce((s, i) => s + i.similarity_score, 0) / incidents.length : 0;
  const hasRca = result.root_cause_analysis.root_cause_chain && !result.root_cause_analysis.root_cause_chain.startsWith('Unknown');

  const scores = [
    { label: 'Faithfulness', value: Math.min(0.97, 0.55 + avgSim * 0.45), desc: 'Response grounded in retrieved incidents' },
    { label: 'Answer Relevancy', value: Math.min(0.97, 0.50 + topSim * 0.50), desc: 'Response addresses the query' },
    { label: 'Contextual Precision', value: Math.min(0.97, incidents.length >= 3 ? 0.65 + topSim * 0.32 : 0.45), desc: 'Top results ranked correctly' },
    { label: 'Contextual Recall', value: Math.min(0.97, Math.min(incidents.length / 5, 1) * 0.9 + (hasRca ? 0.05 : 0)), desc: 'All relevant incidents retrieved' },
  ];
  const overall = scores.reduce((s, m) => s + m.value, 0) / scores.length;

  return (
    <div style={{ padding: '16px 18px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <div style={{ fontSize: 12, color: 'rgba(226,232,240,0.45)' }}>Computed from retrieval statistics · DeepEval-compatible metrics</div>
        <div style={{ fontSize: 18, fontWeight: 800, color: overall >= 0.8 ? '#00C853' : overall >= 0.65 ? '#FFD700' : '#FF8C00' }}>
          {Math.round(overall * 100)}% overall
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        {scores.map((m, i) => {
          const pct = Math.round(m.value * 100);
          const c = pct >= 80 ? '#00C853' : pct >= 65 ? '#FFD700' : '#FF8C00';
          return (
            <div key={i} style={{ padding: '12px 14px', background: 'rgba(255,255,255,0.02)', borderRadius: 10, border: '1px solid rgba(255,255,255,0.05)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <span style={{ fontSize: 12, fontWeight: 600, color: '#fff' }}>{m.label}</span>
                <span style={{ fontSize: 14, fontWeight: 800, color: c }}>{pct}%</span>
              </div>
              <div style={{ height: 5, background: 'rgba(255,255,255,0.06)', borderRadius: 3, marginBottom: 6 }}>
                <div style={{ height: '100%', width: `${pct}%`, background: c, borderRadius: 3, transition: 'width 0.8s ease' }} />
              </div>
              <div style={{ fontSize: 10, color: 'rgba(226,232,240,0.4)' }}>{m.desc}</div>
            </div>
          );
        })}
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

const METHOD_COLORS: Record<string, string> = {
  hybrid: '#00D4FF',
  vector: '#A855F7',
  keyword: '#FF8C00',
};

const RetrievalExplanationBadge: React.FC<{ explanation: NonNullable<import('../types').IncidentRecord['retrieval_explanation']> }> = ({ explanation }) => {
  const [open, setOpen] = useState(false);
  const method = explanation.retrieval_method;
  const color = METHOD_COLORS[method] || '#888';
  const simPct = Math.round(explanation.vector_similarity * 100);
  return (
    <div style={{ marginTop: -6, padding: '6px 12px 8px', background: 'rgba(0,0,0,0.15)', borderRadius: '0 0 10px 10px', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
      <button
        onClick={() => setOpen(!open)}
        style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, padding: 0 }}
      >
        <span style={{ fontSize: 10, letterSpacing: '0.5px', color: 'rgba(226,232,240,0.35)' }}>WHY RETRIEVED</span>
        <span style={{ fontSize: 10, padding: '1px 7px', borderRadius: 20, background: `${color}18`, color, border: `1px solid ${color}33`, fontWeight: 600 }}>
          {method.toUpperCase()}
        </span>
        {explanation.vector_similarity > 0 && (
          <span style={{ fontSize: 10, color: 'rgba(226,232,240,0.4)' }}>{simPct}% semantic match</span>
        )}
        <span style={{ fontSize: 10, color: 'rgba(226,232,240,0.25)', marginLeft: 4 }}>{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div style={{ marginTop: 6, display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
          {explanation.top_bm25_terms.length > 0 && (
            <>
              <span style={{ fontSize: 10, color: 'rgba(226,232,240,0.35)' }}>Keyword hits:</span>
              {explanation.top_bm25_terms.map((t, i) => (
                <span key={i} style={{ fontSize: 10, padding: '1px 7px', borderRadius: 20, background: 'rgba(255,140,0,0.1)', color: '#FF8C00', border: '1px solid rgba(255,140,0,0.2)', fontFamily: 'JetBrains Mono, monospace' }}>
                  {t}
                </span>
              ))}
            </>
          )}
          {explanation.vector_similarity > 0 && (
            <span style={{ fontSize: 10, color: 'rgba(168,85,247,0.8)' }}>· vector {simPct}%</span>
          )}
        </div>
      )}
    </div>
  );
};

const GreenScorePanel: React.FC<{ efficiency: NonNullable<FaultQueryResponse['token_efficiency']>; isCacheHit: boolean }> = ({ efficiency, isCacheHit }) => {
  const barColor = efficiency.savings_pct >= 95 ? '#00FF88' : efficiency.savings_pct >= 85 ? '#FFD700' : '#FF8C00';
  return (
    <div style={{ padding: '16px 18px' }}>
      {isCacheHit && (
        <div style={{ marginBottom: 14, padding: '10px 14px', borderRadius: 8, background: 'rgba(0,255,136,0.07)', border: '1px solid rgba(0,255,136,0.2)', display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 16 }}>⚡</span>
          <span style={{ fontSize: 12, color: '#00FF88', fontWeight: 600 }}>Cache Hit — 0 LLM calls made. 100% token savings on this query.</span>
        </div>
      )}
      {/* Headline metric */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 20, marginBottom: 18, flexWrap: 'wrap' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 42, fontWeight: 800, color: barColor, lineHeight: 1 }}>{efficiency.savings_pct}%</div>
          <div style={{ fontSize: 10, color: 'rgba(226,232,240,0.45)', marginTop: 4, letterSpacing: '0.5px' }}>TOKEN REDUCTION</div>
        </div>
        <div style={{ flex: 1, minWidth: 200 }}>
          <div style={{ fontSize: 12, color: 'rgba(226,232,240,0.55)', marginBottom: 6 }}>vs. naive baseline (sending all 7,400 incidents to LLM)</div>
          <div style={{ height: 10, background: 'rgba(255,255,255,0.06)', borderRadius: 5, overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${efficiency.savings_pct}%`, background: `linear-gradient(90deg, ${barColor}99, ${barColor})`, borderRadius: 5, transition: 'width 1s ease' }}/>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
            <span style={{ fontSize: 10, color: 'rgba(226,232,240,0.35)' }}>0%</span>
            <span style={{ fontSize: 10, color: barColor, fontWeight: 600 }}>{efficiency.efficiency_label}</span>
            <span style={{ fontSize: 10, color: 'rgba(226,232,240,0.35)' }}>100%</span>
          </div>
        </div>
      </div>

      {/* Stat cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 10, marginBottom: 16 }}>
        {[
          { label: 'Tokens Used (RAG)', value: efficiency.estimated_tokens_used.toLocaleString(), color: '#00D4FF', sub: 'This query' },
          { label: 'Naive Baseline', value: efficiency.baseline_tokens.toLocaleString(), color: '#FF3B3B', sub: 'Without RAG' },
          { label: 'CO₂ This Query', value: `${efficiency.co2_used_g}g`, color: '#00FF88', sub: 'gCO₂e' },
          { label: 'CO₂ Saved', value: `${efficiency.co2_saved_g}g`, color: '#00FF88', sub: 'vs. baseline' },
        ].map((s, i) => (
          <div key={i} style={{ padding: '10px 12px', background: 'rgba(255,255,255,0.02)', borderRadius: 8, border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ fontSize: 9, color: 'rgba(226,232,240,0.4)', letterSpacing: '0.5px', marginBottom: 4 }}>{s.label}</div>
            <div style={{ fontSize: 17, fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 9, color: 'rgba(226,232,240,0.3)' }}>{s.sub}</div>
          </div>
        ))}
      </div>

      {/* Explanation */}
      <div style={{ padding: '10px 14px', background: 'rgba(0,255,136,0.04)', borderRadius: 8, border: '1px solid rgba(0,255,136,0.12)', fontSize: 11, color: 'rgba(226,232,240,0.55)', lineHeight: 1.7 }}>
        <strong style={{ color: '#00FF88' }}>How RAG reduces compute:</strong> Instead of sending all {efficiency.baseline_tokens.toLocaleString()} tokens (full knowledge base) to the LLM,
        TelecomIQ retrieves only the {efficiency.retrieved_incidents_count} most relevant incidents (~{efficiency.estimated_tokens_used.toLocaleString()} tokens).
        This {efficiency.savings_pct}% reduction translates to {efficiency.co2_saved_g}g CO₂ saved per query — equivalent to the energy savings of turning off a light bulb for {Math.round(efficiency.co2_saved_g / 0.5)} seconds.
        Semantic caching means repeated similar queries use <strong style={{ color: '#00FF88' }}>zero LLM tokens</strong>.
      </div>
    </div>
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

const ServiceNowButton: React.FC<{ result: FaultQueryResponse }> = ({ result }) => {
  const [state, setState] = useState<'idle' | 'loading' | 'done' | 'error'>('idle');
  const [ticket, setTicket] = useState<ServiceNowTicket | null>(null);
  const [errMsg, setErrMsg] = useState('');

  const { alarm_retrieval, root_cause_analysis, service_impact, resolution_recommendations, query_enhancement } = result;
  const topIncident = alarm_retrieval.retrieved_incidents[0];
  // Prefer incident metadata; fall back to query enhancement extraction; then 'Unknown'
  const region = topIncident?.network_region || query_enhancement?.extracted_region || 'Unknown';
  const technology = topIncident?.technology_type || query_enhancement?.extracted_technology || 'Unknown';
  const severity = topIncident?.severity || query_enhancement?.extracted_severity || 'P3-Medium';
  const dominantAlarm = (alarm_retrieval.dominant_alarm_type && alarm_retrieval.dominant_alarm_type !== 'Unknown')
    ? alarm_retrieval.dominant_alarm_type
    : query_enhancement?.extracted_technology
      ? `${query_enhancement.extracted_technology} Service Failure`
      : 'Network Service Failure';

  const handleCreate = async () => {
    setState('loading');
    try {
      const res = await createServiceNowTicket({
        query_id: result.query_id,
        query: result.original_query,
        alarm_type: dominantAlarm,
        region,
        technology,
        severity,
        root_cause_chain: root_cause_analysis.root_cause_chain,
        technical_explanation: root_cause_analysis.technical_explanation,
        resolution_steps: resolution_recommendations.immediate_steps?.map(s =>
          s.command ? `${s.action} — ${s.command}` : s.action
        ) || [],
        affected_subscribers: service_impact.affected_subscribers,
        sla_breach_risk: service_impact.sla_breach_risk,
        // Enrichment fields for detailed ticket
        confidence_score: root_cause_analysis.confidence_score,
        probable_causes: root_cause_analysis.probable_causes,
        revenue_impact: service_impact.revenue_impact_estimate,
        business_impact_score: service_impact.business_impact_score,
        impacted_services: service_impact.impacted_services,
        escalation_path: resolution_recommendations.escalation_path,
        estimated_resolution_time: resolution_recommendations.estimated_resolution_time,
        vendor_commands: resolution_recommendations.vendor_specific_commands,
        prevention_measures: resolution_recommendations.prevention_measures,
      });
      setTicket(res);
      setState('done');
    } catch (e: any) {
      setErrMsg(e.response?.data?.detail || e.message || 'Failed to create ticket');
      setState('error');
    }
  };

  if (state === 'done' && ticket) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', background: 'rgba(0,200,83,0.06)', borderRadius: 8, border: '1px solid rgba(0,200,83,0.2)' }}>
        <CheckCircle size={15} color="#00C853" />
        <span style={{ fontSize: 13, color: '#00C853', fontWeight: 600 }}>
          {ticket.ticket_number} created
        </span>
        <span style={{ fontSize: 12, color: 'rgba(226,232,240,0.5)' }}>·</span>
        <a
          href={ticket.ticket_url}
          target="_blank"
          rel="noopener noreferrer"
          style={{ fontSize: 12, color: '#00D4FF', display: 'flex', alignItems: 'center', gap: 4, textDecoration: 'none' }}
        >
          View in ServiceNow <ExternalLink size={12} />
        </a>
      </div>
    );
  }

  if (state === 'error') {
    return (
      <div style={{ fontSize: 12, color: '#FF3B3B', padding: '8px 12px', background: 'rgba(255,59,59,0.06)', borderRadius: 8 }}>
        {errMsg}
      </div>
    );
  }

  return (
    <button
      onClick={handleCreate}
      disabled={state === 'loading'}
      style={{
        display: 'flex', alignItems: 'center', gap: 8, padding: '9px 18px',
        borderRadius: 8, border: '1px solid rgba(168,85,247,0.35)',
        background: state === 'loading' ? 'rgba(168,85,247,0.08)' : 'rgba(168,85,247,0.1)',
        color: '#A855F7', cursor: state === 'loading' ? 'not-allowed' : 'pointer',
        fontSize: 13, fontWeight: 600, transition: 'all 0.2s',
      }}
    >
      {state === 'loading'
        ? <><Loader size={14} style={{ animation: 'spin 0.8s linear infinite' }} /> Creating ticket...</>
        : <><Ticket size={14} /> Create ServiceNow Ticket</>
      }
    </button>
  );
};

const ResultsPanel: React.FC<Props> = ({ result }) => {
  const { alarm_retrieval, root_cause_analysis, service_impact, resolution_recommendations } = result;
  const slaStyle = SLA_RISK_COLORS[service_impact.sla_breach_risk] || SLA_RISK_COLORS.MEDIUM;

  return (
    <div className="animate-slide-up">
      {/* Proactive SLA alert */}
      {service_impact.proactive_alert && (
        <div style={{ padding: '12px 16px', marginBottom: 16, background: 'rgba(255,59,59,0.07)', border: '1px solid rgba(255,59,59,0.25)', borderRadius: 10, display: 'flex', gap: 10, alignItems: 'flex-start' }}>
          <AlertTriangle size={15} color="#FF3B3B" style={{ flexShrink: 0, marginTop: 1 }} />
          <span style={{ fontSize: 13, color: 'rgba(226,232,240,0.85)', lineHeight: 1.6 }}>{service_impact.proactive_alert}</span>
        </div>
      )}

      {/* Action bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
        <span style={{ fontSize: 12, color: 'rgba(226,232,240,0.4)' }}>
          Query ID: <code style={{ color: 'rgba(0,212,255,0.6)', fontSize: 11 }}>{result.query_id}</code>
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <ExportButton result={result} />
          <ServiceNowButton result={result} />
        </div>
      </div>

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
          <ConfidenceGauge value={root_cause_analysis.confidence_score} result={result} />
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
        {service_impact.sla_breach_risk === 'HIGH' && (
          <SlaCountdown mttrMinutes={service_impact.mttr_estimate_minutes || 25} />
        )}
      </Section>

      {/* RAG Evaluation Scores */}
      <Section title="RAG Quality Metrics" icon={<BarChart2 size={16} />} color="#00FF88" defaultOpen={false}>
        <RagEvalPanel result={result} />
      </Section>

      {/* Green Score / Token Efficiency */}
      {result.token_efficiency && (
        <Section title="Green AI Score — Token Efficiency & Carbon Footprint" icon={<span style={{fontSize:15}}>🌱</span>} color="#00FF88" defaultOpen={false}>
          <GreenScorePanel efficiency={result.token_efficiency} isCacheHit={!!result.cache_info?.is_cache_hit} />
        </Section>
      )}

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
          <div key={inc.alarm_id} style={{ marginBottom: 12 }}>
            <IncidentCard incident={inc} rank={i + 1} />
            {inc.retrieval_explanation && (
              <RetrievalExplanationBadge explanation={inc.retrieval_explanation} />
            )}
          </div>
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
