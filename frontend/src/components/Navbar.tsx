import React, { useState, useEffect } from 'react';
import { Activity, Zap, BarChart2, Clock, Wifi } from 'lucide-react';
import { getHealth } from '../services/api';
import { HealthResponse } from '../types';

interface NavbarProps {
  currentPage: 'home' | 'dashboard' | 'history';
  onNavigate: (page: 'home' | 'dashboard' | 'history') => void;
}

const Navbar: React.FC<NavbarProps> = ({ currentPage, onNavigate }) => {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => {});
    const interval = setInterval(() => getHealth().then(setHealth).catch(() => {}), 30000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { id: 'home' as const, label: 'Fault Analysis', icon: <Zap size={16} /> },
    { id: 'dashboard' as const, label: 'Dashboard', icon: <BarChart2 size={16} /> },
    { id: 'history' as const, label: 'Query History', icon: <Clock size={16} /> },
  ];

  return (
    <nav
      style={{
        background: 'rgba(13, 18, 33, 0.95)',
        borderBottom: '1px solid rgba(0,212,255,0.15)',
        backdropFilter: 'blur(20px)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}
    >
      <div style={{ maxWidth: 1400, margin: '0 auto', padding: '0 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 64 }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div
            style={{
              width: 36, height: 36, borderRadius: 8,
              background: 'linear-gradient(135deg, #00D4FF20, #0066CC40)',
              border: '1px solid rgba(0,212,255,0.4)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            <Activity size={20} color="#00D4FF" />
          </div>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#fff', letterSpacing: '-0.3px' }}>
              TelecomIQ
            </div>
            <div style={{ fontSize: 10, color: 'rgba(0,212,255,0.7)', letterSpacing: '1.5px', textTransform: 'uppercase' }}>
              Fault Intelligence
            </div>
          </div>
        </div>

        {/* Nav items */}
        <div style={{ display: 'flex', gap: 4 }}>
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              style={{
                display: 'flex', alignItems: 'center', gap: 6,
                padding: '8px 16px', borderRadius: 8, border: 'none', cursor: 'pointer',
                fontSize: 13, fontWeight: 500, transition: 'all 0.2s',
                background: currentPage === item.id ? 'rgba(0,212,255,0.12)' : 'transparent',
                color: currentPage === item.id ? '#00D4FF' : 'rgba(226,232,240,0.7)',
                outline: currentPage === item.id ? '1px solid rgba(0,212,255,0.3)' : '1px solid transparent',
              }}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </div>

        {/* Status indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '6px 12px', borderRadius: 20,
              background: health?.status === 'healthy' ? 'rgba(0,200,83,0.1)' : 'rgba(255,59,59,0.1)',
              border: `1px solid ${health?.status === 'healthy' ? 'rgba(0,200,83,0.3)' : 'rgba(255,59,59,0.3)'}`,
            }}
          >
            <div
              style={{
                width: 7, height: 7, borderRadius: '50%',
                background: health?.status === 'healthy' ? '#00C853' : '#FF3B3B',
                boxShadow: `0 0 6px ${health?.status === 'healthy' ? '#00C853' : '#FF3B3B'}`,
              }}
            />
            <span style={{ fontSize: 11, color: health?.status === 'healthy' ? '#00C853' : '#FF3B3B', fontWeight: 600 }}>
              {health?.status === 'healthy' ? 'ONLINE' : health ? 'DEGRADED' : 'CONNECTING'}
            </span>
          </div>
          {health && (
            <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.4)', display: 'flex', alignItems: 'center', gap: 4 }}>
              <Wifi size={12} />
              {health.total_indexed_incidents.toLocaleString()} incidents
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
