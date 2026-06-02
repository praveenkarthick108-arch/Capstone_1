import React, { useEffect, useState } from 'react';
import { AnalyticsResponse } from '../types';
import { getAnalytics } from '../services/api';
import {
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { Activity, AlertTriangle, Users, Clock, TrendingUp, RefreshCw } from 'lucide-react';

const SEVERITY_COLORS: Record<string, string> = {
  'P1-Critical': '#FF3B3B',
  'P2-High': '#FF8C00',
  'P3-Medium': '#FFD700',
  'P4-Low': '#00C853',
};

const TECH_COLORS = ['#00D4FF', '#A855F7', '#F59E0B', '#00FF88', '#FF6B6B', '#4ECDC4'];
const REGION_COLORS = ['#00D4FF', '#A855F7', '#F59E0B', '#00FF88', '#FF8C00'];
const VENDOR_COLORS = ['#00D4FF', '#FF8C00', '#FF3B3B', '#A855F7', '#00C853'];

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

const Dashboard: React.FC = () => {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    getAnalytics().then(setData).catch(console.error).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  if (loading) {
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
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([name, value]) => ({ name: name.replace(' ', '\n'), value }));

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: '40px 24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 32 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: '#fff' }}>Analytics Dashboard</h2>
          <p style={{ margin: '4px 0 0', fontSize: 13, color: 'rgba(226,232,240,0.45)' }}>
            Incident intelligence across {data.total_incidents.toLocaleString()} historical records
          </p>
        </div>
        <button onClick={load} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 16px', borderRadius: 8, border: '1px solid rgba(0,212,255,0.2)', background: 'transparent', color: '#00D4FF', cursor: 'pointer', fontSize: 13 }}>
          <RefreshCw size={14} />Refresh
        </button>
      </div>

      {/* KPI row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 14, marginBottom: 28 }}>
        <KPICard label="Total Incidents" value={data.total_incidents} sub="In knowledge base" icon={<Activity size={18} />} color="#00D4FF" />
        <KPICard label="Avg Outage" value={`${Math.round(data.avg_outage_duration)}m`} sub="Minutes per incident" icon={<Clock size={18} />} color="#FF8C00" />
        <KPICard label="Avg Subscribers" value={Math.round(data.avg_affected_subscribers)} sub="Per incident" icon={<Users size={18} />} color="#A855F7" />
        <KPICard label="Critical Incidents" value={data.severity_distribution['P1-Critical'] || 0} sub="Highest priority" icon={<AlertTriangle size={18} />} color="#FF3B3B" />
        <KPICard label="Active Regions" value={Object.keys(data.region_distribution).length} sub="Coverage areas" icon={<TrendingUp size={18} />} color="#00FF88" />
      </div>

      {/* Charts row 1 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 16 }}>
        <div className="glass-card" style={{ padding: '20px 20px' }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 16 }}>Severity Distribution</div>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={severityData} cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={3} dataKey="value">
                {severityData.map((entry, i) => (
                  <Cell key={i} fill={SEVERITY_COLORS[entry.name] || '#00D4FF'} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend formatter={(value) => <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.65)' }}>{value}</span>} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-card" style={{ padding: '20px 20px' }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 16 }}>Technology Distribution</div>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={techData} cx="50%" cy="50%" outerRadius={85} paddingAngle={2} dataKey="value">
                {techData.map((entry, i) => (
                  <Cell key={i} fill={TECH_COLORS[i % TECH_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend formatter={(value) => <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.65)' }}>{value}</span>} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-card" style={{ padding: '20px 20px' }}>
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
        <div className="glass-card" style={{ padding: '20px 20px' }}>
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

        <div className="glass-card" style={{ padding: '20px 20px' }}>
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
        <div className="glass-card" style={{ padding: '20px 20px' }}>
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

        <div className="glass-card" style={{ padding: '20px 20px' }}>
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
    </div>
  );
};

export default Dashboard;
