import React from 'react';
import { QueryFilters } from '../types';
import { Filter, X } from 'lucide-react';

interface Props {
  filters: QueryFilters;
  onChange: (filters: QueryFilters) => void;
}

const OPTIONS = {
  network_region: ['North', 'South', 'East', 'West', 'Central'],
  technology_type: ['5G-NR', '4G-LTE', '3G-UMTS', 'Fiber', 'MPLS', 'SD-WAN'],
  severity: ['P1-Critical', 'P2-High', 'P3-Medium', 'P4-Low'],
  device_vendor: ['Ericsson', 'Nokia', 'Huawei', 'Cisco', 'Juniper'],
};

const LABELS: Record<string, string> = {
  network_region: 'Region',
  technology_type: 'Technology',
  severity: 'Severity',
  device_vendor: 'Vendor',
};

const SEVERITY_COLORS: Record<string, string> = {
  'P1-Critical': '#FF3B3B',
  'P2-High': '#FF8C00',
  'P3-Medium': '#FFD700',
  'P4-Low': '#00C853',
};

const FilterPanel: React.FC<Props> = ({ filters, onChange }) => {
  const activeCount = Object.values(filters).filter(Boolean).length;

  const setFilter = (key: keyof QueryFilters, value: string) => {
    onChange({ ...filters, [key]: filters[key] === value ? undefined : value });
  };

  const clearAll = () => onChange({});

  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <Filter size={14} color="rgba(0,212,255,0.7)" />
        <span style={{ fontSize: 12, color: 'rgba(0,212,255,0.7)', fontWeight: 600, letterSpacing: '0.5px' }}>
          FILTERS
        </span>
        {activeCount > 0 && (
          <button
            onClick={clearAll}
            style={{
              marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 4,
              fontSize: 11, color: 'rgba(226,232,240,0.5)', background: 'none', border: 'none',
              cursor: 'pointer', padding: '2px 8px', borderRadius: 6,
              transition: 'color 0.2s',
            }}
          >
            <X size={11} /> Clear {activeCount}
          </button>
        )}
      </div>
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        {(Object.keys(OPTIONS) as Array<keyof typeof OPTIONS>).map((key) => (
          <div key={key} style={{ minWidth: 0 }}>
            <div style={{ fontSize: 10, color: 'rgba(226,232,240,0.4)', marginBottom: 6, letterSpacing: '0.5px', textTransform: 'uppercase' }}>
              {LABELS[key]}
            </div>
            <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
              {OPTIONS[key].map((opt) => {
                const isActive = filters[key] === opt;
                const color = key === 'severity' ? SEVERITY_COLORS[opt] : '#00D4FF';
                return (
                  <button
                    key={opt}
                    onClick={() => setFilter(key, opt)}
                    style={{
                      padding: '4px 10px', borderRadius: 20, fontSize: 11,
                      border: `1px solid ${isActive ? color : 'rgba(255,255,255,0.1)'}`,
                      background: isActive ? `${color}18` : 'transparent',
                      color: isActive ? color : 'rgba(226,232,240,0.55)',
                      cursor: 'pointer', transition: 'all 0.2s', fontWeight: isActive ? 600 : 400,
                    }}
                  >
                    {opt}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default FilterPanel;
