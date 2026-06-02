import React, { useState } from 'react';
import { IncidentRecord } from '../types';
import { ChevronDown, ChevronUp, MapPin, Cpu, Clock, Users, AlertTriangle } from 'lucide-react';

interface Props {
  incident: IncidentRecord;
  rank: number;
}

const severityBadgeClass: Record<string, string> = {
  'P1-Critical': 'badge-critical',
  'P2-High': 'badge-high',
  'P3-Medium': 'badge-medium',
  'P4-Low': 'badge-low',
};

const IncidentCard: React.FC<Props> = ({ incident, rank }) => {
  const [expanded, setExpanded] = useState(false);
  const badgeClass = severityBadgeClass[incident.severity] || 'badge-medium';
  const similarityPct = Math.round(incident.similarity_score * 100);

  return (
    <div
      className="glass-card glass-hover"
      style={{ marginBottom: 10, transition: 'all 0.2s' }}
    >
      <div
        style={{ padding: '14px 16px', cursor: 'pointer', display: 'flex', alignItems: 'flex-start', gap: 12 }}
        onClick={() => setExpanded(!expanded)}
      >
        {/* Rank + similarity */}
        <div style={{ textAlign: 'center', flexShrink: 0, minWidth: 48 }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: '#00D4FF' }}>#{rank}</div>
          <div style={{ fontSize: 10, color: 'rgba(226,232,240,0.5)' }}>{similarityPct}% match</div>
          <div
            style={{
              marginTop: 4, height: 3, borderRadius: 2,
              background: `linear-gradient(90deg, #00D4FF ${similarityPct}%, rgba(255,255,255,0.08) ${similarityPct}%)`,
            }}
          />
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 12, fontFamily: 'monospace', color: 'rgba(0,212,255,0.8)' }}>
              {incident.alarm_id}
            </span>
            <span className={badgeClass} style={{ fontSize: 10, padding: '2px 8px', borderRadius: 20, fontWeight: 600 }}>
              {incident.severity}
            </span>
            <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.5)', background: 'rgba(255,255,255,0.04)', padding: '2px 8px', borderRadius: 20, border: '1px solid rgba(255,255,255,0.08)' }}>
              {incident.alarm_type}
            </span>
          </div>

          <p style={{ margin: 0, fontSize: 13, color: 'rgba(226,232,240,0.85)', lineHeight: 1.5, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: expanded ? undefined : 2, WebkitBoxOrient: 'vertical' }}>
            {incident.incident_description}
          </p>

          <div style={{ display: 'flex', gap: 16, marginTop: 10, flexWrap: 'wrap' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: 'rgba(226,232,240,0.5)' }}>
              <MapPin size={11} />{incident.network_region}
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: 'rgba(226,232,240,0.5)' }}>
              <Cpu size={11} />{incident.technology_type} · {incident.device_vendor}
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: 'rgba(226,232,240,0.5)' }}>
              <Clock size={11} />{incident.outage_duration}min outage
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: 'rgba(226,232,240,0.5)' }}>
              <Users size={11} />{incident.affected_subscribers?.toLocaleString()} subs
            </span>
          </div>
        </div>

        <div style={{ color: 'rgba(226,232,240,0.4)', flexShrink: 0 }}>
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </div>

      {expanded && (
        <div
          style={{ borderTop: '1px solid rgba(0,212,255,0.1)', padding: '14px 16px', animation: 'fadeIn 0.2s' }}
          className="animate-fade-in"
        >
          <div style={{ fontSize: 12, color: 'rgba(0,212,255,0.7)', marginBottom: 8, fontWeight: 600, letterSpacing: '0.5px' }}>
            RESOLUTION NOTES
          </div>
          <p style={{ margin: 0, fontSize: 13, color: 'rgba(226,232,240,0.7)', lineHeight: 1.6 }}>
            {incident.resolution_notes}
          </p>
          <div style={{ marginTop: 10, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.4)' }}>
              Impact: {incident.service_impact}
            </span>
            {incident.timestamp && (
              <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.4)' }}>
                · {new Date(incident.timestamp).toLocaleDateString()}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default IncidentCard;
