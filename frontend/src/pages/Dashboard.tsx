import React, { useEffect, useState, useCallback } from 'react';
import { AnalyticsResponse, PredictionResponse } from '../types';
import { getAnalytics, getPredictions } from '../services/api';
import {
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
} from 'recharts';
import {
  Activity, AlertTriangle, Users, Clock, TrendingUp,
  RefreshCw, Shield, Zap, MapPin,
} from 'lucide-react';

const SEVERITY_COLORS: Record<string, string> = {
  'P1-Critical': '#FF3B3B',
  'P2-High': '#FF8C00',
  'P3-Medium': '#FFD700',
  'P4-Low': '#00C853',
};
const RISK_COLORS: Record<string, string> = {
  CRITICAL: '#FF3B3B',
  HIGH: '#FF8C00',
  MEDIUM: '#FFD700',
  LOW: '#00C853',
};
const TECH_COLORS = ['#00D4FF', '#A855F7', '#F59E0B', '#00FF88', '#FF6B6B', '#4ECDC4'];
const REGION_COLORS = ['#00D4FF', '#A855F7', '#F59E0B', '#00FF88', '#FF8C00'];
const VENDOR_COLORS = ['#00D4FF', '#FF8C00', '#FF3B3B', '#A855F7', '#00C853'];

const AUTO_REFRESH_SECONDS = 30;

const CountdownTimer: React.FC<{ onRefresh: () => void; loading: boolean }> = ({ onRefresh, loading }) => {
  const [countdown, setCountdown] = useState(AUTO_REFRESH_SECONDS);

  useEffect(() => {
    setCountdown(AUTO_REFRESH_SECONDS);
  }, [loading]);

  useEffect(() => {
    const tick = setInterval(() => {
      setCountdown(c => {
        if (c <= 1) { onRefresh(); return AUTO_REFRESH_SECONDS; }
        return c - 1;
      });
    }, 1000);
    return () => clearInterval(tick);
  }, [onRefresh]);

  return <div style={{ fontSize: 12, color: 'rgba(226,232,240,0.35)' }}>Auto-refresh in {countdown}s</div>;
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: 'rgba(13,18,33,0.95)', border: '1px solid rgba(0,212,255,0.2)', borderRadius: 8, padding: '10px 14px' }}>
      <div style={{ fontSize: 12, color: 'rgba(226,232,240,0.6)', marginBottom: 4 }}>{label}</div>
      {payload.map((p: any, i: number) => (
        <div key={i} style={{ fontSize: 13, fontWeight: 600, color: p.fill || p.color || '#00D4FF' }}>
          {p.name}: {typeof p.value === 'number' ? p.value.toLocaleString() : p.value}
        </div>
      ))}
    </div>
  );
};

const KPICard: React.FC<{ label: string; value: string | number; sub?: string; icon: React.ReactNode; color?: string }> =
  ({ label, value, sub, icon, color = '#00D4FF' }) => (
    <div className="glass-card" style={{ padding: '20px 20px' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 12 }}>
        <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.45)', letterSpacing: '0.5px', textTransform: 'uppercase' }}>{label}</div>
        <div style={{ color, opacity: 0.7 }}>{icon}</div>
      </div>
      <div style={{ fontSize: 28, fontWeight: 800, color, letterSpacing: '-0.5px' }}>{typeof value === 'number' ? value.toLocaleString() : value}</div>
      {sub && <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.35)', marginTop: 4 }}>{sub}</div>}
    </div>
  );

const RiskBadge: React.FC<{ level: string }> = ({ level }) => (
  <span style={{
    fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 20, letterSpacing: '0.5px',
    background: `${RISK_COLORS[level] || '#888'}22`,
    color: RISK_COLORS[level] || '#888',
    border: `1px solid ${RISK_COLORS[level] || '#888'}44`,
  }}>
    {level}
  </span>
);

const Dashboard: React.FC = () => {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [predictions, setPredictions] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'prediction' | 'sla' | 'correlation'>('overview');

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([getAnalytics(), getPredictions()])
      .then(([analytics, preds]) => {
        setData(analytics);
        setPredictions(preds);
        setLastRefreshed(new Date());
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading && !data) {
    return (
      <div style={{ maxWidth: 1400, margin: '0 auto', padding: '80px 24px', textAlign: 'center' }}>
        <div style={{ width: 40, height: 40, border: '3px solid rgba(0,212,255,0.2)', borderTopColor: '#00D4FF', borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 16px' }} />
        <div style={{ color: 'rgba(226,232,240,0.5)' }}>Loading analytics...</div>
        <style>{`@keyframes spin{from{transform:rotate(0)}to{transform:rotate(360deg)}}`}</style>
      </div>
    );
  }
  if (!data) return null;

  const severityData = Object.entries(data.severity_distribution).map(([name, value]) => ({ name, value }));
  const techData = Object.entries(data.technology_distribution).map(([name, value]) => ({ name, value }));
  const regionData = Object.entries(data.region_distribution).map(([name, value]) => ({ name, value }));
  const vendorData = Object.entries(data.vendor_distribution).map(([name, value]) => ({ name, value }));
  const alarmData = Object.entries(data.alarm_type_distribution)
    .sort((a, b) => b[1] - a[1]).slice(0, 8)
    .map(([name, value]) => ({ name: name.length > 14 ? name.slice(0, 14) + '…' : name, value }));

  const riskByRegion = (data.risk_by_region || []).map(r => ({
    region: r.region,
    score: r.risk_score,
    fill: RISK_COLORS[r.risk_level] || '#888',
  }));

  const tabs = [
    { key: 'overview', label: 'Overview' },
    { key: 'prediction', label: 'Risk Forecast' },
    { key: 'sla', label: 'SLA Intelligence' },
    { key: 'correlation', label: 'Cross-Region' },
  ] as const;

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: '40px 24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: '#fff' }}>Analytics Dashboard</h2>
          <p style={{ margin: '4px 0 0', fontSize: 13, color: 'rgba(226,232,240,0.45)' }}>
            {data.total_incidents.toLocaleString()} historical incidents
            {lastRefreshed && (
              <span style={{ marginLeft: 8 }}>· Updated {lastRefreshed.toLocaleTimeString()}</span>
            )}
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <CountdownTimer onRefresh={load} loading={loading} />
          <button
            onClick={load}
            style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 16px', borderRadius: 8, border: '1px solid rgba(0,212,255,0.2)', background: 'transparent', color: '#00D4FF', cursor: 'pointer', fontSize: 13 }}
          >
            <RefreshCw size={14} style={loading ? { animation: 'spin 0.8s linear infinite' } : {}} />
            Refresh
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: 0 }}>
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            style={{
              padding: '8px 18px', fontSize: 13, fontWeight: 500, cursor: 'pointer',
              background: 'transparent', border: 'none', borderBottom: activeTab === t.key ? '2px solid #00D4FF' : '2px solid transparent',
              color: activeTab === t.key ? '#00D4FF' : 'rgba(226,232,240,0.45)',
              transition: 'all 0.2s', marginBottom: -1,
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ── OVERVIEW TAB ── */}
      {activeTab === 'overview' && (
        <>
          {/* KPI row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 14, marginBottom: 28 }}>
            <KPICard label="Total Incidents" value={data.total_incidents} sub="In knowledge base" icon={<Activity size={18} />} color="#00D4FF" />
            <KPICard label="Avg Outage" value={`${Math.round(data.avg_outage_duration)}m`} sub="Minutes per incident" icon={<Clock size={18} />} color="#FF8C00" />
            <KPICard label="Avg Subscribers" value={Math.round(data.avg_affected_subscribers)} sub="Per incident" icon={<Users size={18} />} color="#A855F7" />
            <KPICard label="Critical Incidents" value={data.severity_distribution['P1-Critical'] || 0} sub="Highest priority" icon={<AlertTriangle size={18} />} color="#FF3B3B" />
            <KPICard label="SLA Breach Rate" value={`${data.sla_breach_rate_pct}%`} sub="Outages >30 min" icon={<Shield size={18} />} color={data.sla_breach_rate_pct > 20 ? '#FF3B3B' : data.sla_breach_rate_pct > 10 ? '#FF8C00' : '#00FF88'} />
            <KPICard label="Active Regions" value={Object.keys(data.region_distribution).length} sub="Coverage areas" icon={<TrendingUp size={18} />} color="#00FF88" />
          </div>

          {/* Charts row 1 */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 16 }}>
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 16 }}>Severity Distribution</div>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={severityData} cx="50%" cy="43%" innerRadius={55} outerRadius={82} paddingAngle={3} dataKey="value">
                    {severityData.map((entry, i) => <Cell key={i} fill={SEVERITY_COLORS[entry.name] || '#00D4FF'} />)}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend formatter={(v) => <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.65)' }}>{v}</span>} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 16 }}>Technology Distribution</div>
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie data={techData} cx="50%" cy="40%" outerRadius={78} paddingAngle={2} dataKey="value">
                    {techData.map((_, i) => <Cell key={i} fill={TECH_COLORS[i % TECH_COLORS.length]} />)}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend formatter={(v) => <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.65)' }}>{v}</span>} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 16 }}>Region Distribution</div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={regionData} layout="vertical">
                  <XAxis type="number" tick={{ fill: 'rgba(226,232,240,0.4)', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="name" tick={{ fill: 'rgba(226,232,240,0.6)', fontSize: 12 }} axisLine={false} tickLine={false} width={55} />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {regionData.map((_, i) => <Cell key={i} fill={REGION_COLORS[i % REGION_COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Charts row 2 */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16, marginBottom: 16 }}>
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 16 }}>Monthly Incident Trends</div>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={data.monthly_trends}>
                  <XAxis dataKey="month" tick={{ fill: 'rgba(226,232,240,0.4)', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: 'rgba(226,232,240,0.4)', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Line type="monotone" dataKey="incidents" stroke="#00D4FF" strokeWidth={2} dot={{ fill: '#00D4FF', r: 3 }} name="Incidents" />
                  <Line type="monotone" dataKey="avg_duration" stroke="#FF8C00" strokeWidth={2} dot={{ fill: '#FF8C00', r: 3 }} name="Avg Duration (m)" />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 16 }}>Vendor Fault Frequency</div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={vendorData} layout="vertical">
                  <XAxis type="number" tick={{ fill: 'rgba(226,232,240,0.4)', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="name" tick={{ fill: 'rgba(226,232,240,0.6)', fontSize: 12 }} axisLine={false} tickLine={false} width={55} />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {vendorData.map((_, i) => <Cell key={i} fill={VENDOR_COLORS[i % VENDOR_COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Alarm types + Top recurring */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 16 }}>Alarm Type Frequency</div>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={alarmData}>
                  <XAxis dataKey="name" tick={{ fill: 'rgba(226,232,240,0.5)', fontSize: 10 }} axisLine={false} tickLine={false} interval={0} />
                  <YAxis tick={{ fill: 'rgba(226,232,240,0.4)', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                  <Bar dataKey="value" fill="#A855F7" radius={[4, 4, 0, 0]} name="Count" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 16 }}>Top Recurring Issues</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {data.top_recurring_issues.slice(0, 8).map((issue, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px', background: 'rgba(255,255,255,0.02)', borderRadius: 8 }}>
                    <span style={{ fontSize: 11, fontWeight: 700, color: 'rgba(0,212,255,0.5)', minWidth: 20, textAlign: 'right' }}>#{i + 1}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 12, color: '#fff' }}>{issue.alarm_type}</div>
                      <span style={{ fontSize: 10, padding: '1px 6px', borderRadius: 20, ...(issue.severity.includes('P1') ? { background: 'rgba(255,59,59,0.12)', color: '#FF3B3B' } : issue.severity.includes('P2') ? { background: 'rgba(255,140,0,0.12)', color: '#FF8C00' } : { background: 'rgba(255,215,0,0.12)', color: '#FFD700' }) }}>
                        {issue.severity}
                      </span>
                    </div>
                    <span style={{ fontSize: 13, fontWeight: 600, color: 'rgba(0,212,255,0.7)' }}>{issue.count}×</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}

      {/* ── RISK FORECAST TAB ── */}
      {activeTab === 'prediction' && predictions && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            {/* Risk by region bar */}
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                <MapPin size={15} color="#00D4FF" />
                <span style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>Outage Risk by Region</span>
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={riskByRegion} layout="vertical">
                  <XAxis type="number" domain={[0, 100]} tick={{ fill: 'rgba(226,232,240,0.4)', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="region" tick={{ fill: 'rgba(226,232,240,0.6)', fontSize: 12 }} axisLine={false} tickLine={false} width={55} />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                  <Bar dataKey="score" radius={[0, 4, 4, 0]} name="Risk Score">
                    {riskByRegion.map((r, i) => <Cell key={i} fill={r.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Risk by technology */}
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                <Zap size={15} color="#A855F7" />
                <span style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>Outage Risk by Technology</span>
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={predictions.by_technology} layout="vertical">
                  <XAxis type="number" domain={[0, 100]} tick={{ fill: 'rgba(226,232,240,0.4)', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="technology" tick={{ fill: 'rgba(226,232,240,0.6)', fontSize: 12 }} axisLine={false} tickLine={false} width={65} />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                  <Bar dataKey="risk_score" fill="#A855F7" radius={[0, 4, 4, 0]} name="Risk Score" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Region risk cards */}
          <div className="glass-card" style={{ padding: '20px', marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 16 }}>Region Risk Details</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 12 }}>
              {predictions.by_region.map((r, i) => (
                <div key={i} style={{ padding: '14px', background: 'rgba(255,255,255,0.02)', borderRadius: 10, border: `1px solid ${RISK_COLORS[r.risk_level] || '#888'}22` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                    <span style={{ fontSize: 14, fontWeight: 700, color: '#fff' }}>{r.region}</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: 18, fontWeight: 800, color: RISK_COLORS[r.risk_level] || '#888' }}>{r.risk_score}</span>
                      <RiskBadge level={r.risk_level} />
                    </div>
                  </div>
                  <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.5)', marginBottom: 6 }}>
                    {r.incident_count.toLocaleString()} incidents · {r.top_technology} · {r.critical_incident_pct}% critical
                  </div>
                  {r.contributing_factors.map((f, j) => (
                    <div key={j} style={{ fontSize: 11, color: 'rgba(226,232,240,0.5)', display: 'flex', gap: 6, alignItems: 'flex-start', marginBottom: 3 }}>
                      <span style={{ color: RISK_COLORS[r.risk_level], marginTop: 1 }}>•</span>
                      {f}
                    </div>
                  ))}
                  <div style={{ marginTop: 10, fontSize: 11, color: 'rgba(0,212,255,0.7)', padding: '6px 8px', background: 'rgba(0,212,255,0.04)', borderRadius: 6, borderLeft: '2px solid rgba(0,212,255,0.3)' }}>
                    {r.recommended_action}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Top hotspots */}
          <div className="glass-card" style={{ padding: '20px' }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 16 }}>Top Risk Hotspots (Region + Technology)</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {predictions.hotspots.slice(0, 8).map((h, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px', background: 'rgba(255,255,255,0.02)', borderRadius: 8 }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: 'rgba(0,212,255,0.5)', minWidth: 22, textAlign: 'right' }}>#{i + 1}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: '#fff' }}>
                      {h.region} / {h.technology}
                    </div>
                    <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.45)' }}>
                      {h.incident_count} incidents · {h.top_alarm} · avg {h.avg_outage_minutes}min
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 16, fontWeight: 800, color: RISK_COLORS[h.risk_level] }}>{h.risk_score}</span>
                    <RiskBadge level={h.risk_level} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* ── SLA INTELLIGENCE TAB ── */}
      {activeTab === 'sla' && predictions && (
        <>
          {/* SLA KPI row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 14, marginBottom: 24 }}>
            <KPICard
              label="SLA Breach Rate" value={`${predictions.sla_analysis.sla_breach_rate_pct}%`}
              sub={`${predictions.sla_analysis.sla_breaches} incidents >30min`}
              icon={<Shield size={18} />}
              color={predictions.sla_analysis.sla_breach_rate_pct > 20 ? '#FF3B3B' : '#FF8C00'}
            />
            <KPICard
              label="At-Risk Incidents" value={predictions.sla_analysis.at_risk_incidents}
              sub="15-30 min duration (watch zone)"
              icon={<AlertTriangle size={18} />} color="#FFD700"
            />
            <KPICard
              label="Avg Breach Duration" value={`${predictions.sla_analysis.avg_breach_duration_minutes}m`}
              sub={`SLA threshold: ${predictions.sla_analysis.sla_threshold_minutes}min`}
              icon={<Clock size={18} />} color="#FF8C00"
            />
            <KPICard
              label="Est. Total Downtime" value={`${predictions.sla_analysis.estimated_total_downtime_hours}h`}
              sub="Across all incidents"
              icon={<Activity size={18} />} color="#A855F7"
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            {/* Breach probability by severity */}
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 16 }}>SLA Breach Probability by Severity</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {Object.entries(predictions.sla_analysis.breach_probability_by_severity).sort((a, b) => b[1] - a[1]).map(([sev, prob]) => (
                  <div key={sev}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 12, color: SEVERITY_COLORS[sev] || '#888' }}>{sev}</span>
                      <span style={{ fontSize: 12, fontWeight: 700, color: prob > 50 ? '#FF3B3B' : prob > 30 ? '#FF8C00' : '#00C853' }}>{prob}%</span>
                    </div>
                    <div style={{ height: 6, background: 'rgba(255,255,255,0.06)', borderRadius: 3 }}>
                      <div style={{ height: '100%', width: `${prob}%`, background: SEVERITY_COLORS[sev] || '#888', borderRadius: 3, transition: 'width 0.5s ease' }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Breach risk per region heatmap */}
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 16 }}>Predicted Breach Risk by Region</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {Object.entries(predictions.sla_analysis.next_breach_risk_by_region).sort((a, b) => b[1] - a[1]).map(([region, risk]) => (
                  <div key={region}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 12, color: 'rgba(226,232,240,0.7)' }}>{region}</span>
                      <span style={{ fontSize: 12, fontWeight: 700, color: risk > 40 ? '#FF3B3B' : risk > 25 ? '#FF8C00' : '#00C853' }}>{risk.toFixed(1)}%</span>
                    </div>
                    <div style={{ height: 6, background: 'rgba(255,255,255,0.06)', borderRadius: 3 }}>
                      <div style={{ height: '100%', width: `${Math.min(risk, 100)}%`, background: risk > 40 ? '#FF3B3B' : risk > 25 ? '#FF8C00' : '#00C853', borderRadius: 3 }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* SLA breach by region + tech side by side */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 16 }}>SLA Breaches by Region</div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={Object.entries(predictions.sla_analysis.breach_by_region).map(([name, value]) => ({ name, value }))} layout="vertical">
                  <XAxis type="number" tick={{ fill: 'rgba(226,232,240,0.4)', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="name" tick={{ fill: 'rgba(226,232,240,0.6)', fontSize: 12 }} axisLine={false} tickLine={false} width={55} />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                  <Bar dataKey="value" fill="#FF3B3B" radius={[0, 4, 4, 0]} name="Breaches" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 16 }}>SLA Breaches by Technology</div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={Object.entries(predictions.sla_analysis.breach_by_technology).map(([name, value]) => ({ name, value }))} layout="vertical">
                  <XAxis type="number" tick={{ fill: 'rgba(226,232,240,0.4)', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="name" tick={{ fill: 'rgba(226,232,240,0.6)', fontSize: 12 }} axisLine={false} tickLine={false} width={65} />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                  <Bar dataKey="value" fill="#FF8C00" radius={[0, 4, 4, 0]} name="Breaches" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}

      {/* ── CROSS-REGION CORRELATION TAB ── */}
      {activeTab === 'correlation' && data.cross_region_correlation && (
        <>
          {/* Correlation matrix */}
          {data.cross_region_correlation.regions && data.cross_region_correlation.correlation_matrix && (
            <div className="glass-card" style={{ padding: '20px', marginBottom: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 16 }}>
                Cross-Region Fault Correlation Matrix
                <span style={{ fontSize: 11, fontWeight: 400, color: 'rgba(226,232,240,0.4)', marginLeft: 8 }}>
                  (% of shared alarm types between regions)
                </span>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ borderCollapse: 'collapse', fontSize: 12, width: '100%' }}>
                  <thead>
                    <tr>
                      <th style={{ padding: '8px 12px', color: 'rgba(226,232,240,0.4)', textAlign: 'left', fontWeight: 500 }}></th>
                      {data.cross_region_correlation.regions.map(r => (
                        <th key={r} style={{ padding: '8px 12px', color: 'rgba(226,232,240,0.6)', fontWeight: 600, textAlign: 'center' }}>{r}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.cross_region_correlation.regions.map(r1 => (
                      <tr key={r1}>
                        <td style={{ padding: '8px 12px', color: 'rgba(226,232,240,0.6)', fontWeight: 600 }}>{r1}</td>
                        {data.cross_region_correlation.regions!.map(r2 => {
                          const val = data.cross_region_correlation.correlation_matrix![r1]?.[r2] ?? 0;
                          const isdiag = r1 === r2;
                          const intensity = isdiag ? 0.15 : val / 100 * 0.4;
                          return (
                            <td key={r2} style={{
                              padding: '8px 12px', textAlign: 'center', fontWeight: isdiag ? 700 : 400,
                              background: isdiag ? 'rgba(0,212,255,0.1)' : `rgba(168,85,247,${intensity})`,
                              color: isdiag ? '#00D4FF' : val > 70 ? '#FF8C00' : val > 40 ? '#FFD700' : 'rgba(226,232,240,0.6)',
                              borderRadius: 4,
                            }}>
                              {val.toFixed(0)}%
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Propagation patterns */}
          {data.cross_region_correlation.propagation_patterns && (
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 16 }}>
                Cross-Region Fault Propagation Patterns
                <span style={{ fontSize: 11, fontWeight: 400, color: 'rgba(226,232,240,0.4)', marginLeft: 8 }}>
                  (alarm types affecting 3+ regions)
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {data.cross_region_correlation.propagation_patterns.map((p, i) => (
                  <div key={i} style={{ padding: '12px 14px', background: 'rgba(255,255,255,0.02)', borderRadius: 10, border: '1px solid rgba(255,140,0,0.15)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <span style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>{p.alarm_type}</span>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 20, background: 'rgba(255,140,0,0.1)', color: '#FF8C00' }}>
                          {p.spread_count} regions
                        </span>
                        <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 20, background: 'rgba(0,212,255,0.06)', color: 'rgba(0,212,255,0.6)' }}>
                          {p.incident_count} incidents
                        </span>
                      </div>
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {p.affected_regions.map((reg, j) => (
                        <span key={j} style={{ fontSize: 11, padding: '2px 8px', borderRadius: 20, background: 'rgba(168,85,247,0.1)', color: '#A855F7' }}>
                          {reg}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      <style>{`@keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}`}</style>
    </div>
  );
};

export default Dashboard;
