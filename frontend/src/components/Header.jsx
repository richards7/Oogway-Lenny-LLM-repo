import React from 'react';
import { Sparkles, Plus, Database } from 'lucide-react';
import ProviderMenu from './ProviderMenu';

export default function Header({ 
  activeProvider, 
  onProviderChange, 
  onNewSession, 
  config 
}) {
  return (
    <header style={{
      height: '60px',
      padding: '0 16px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      borderBottom: '1px solid var(--border-subtle)',
      background: '#FAF8F5',
      zIndex: 10,
      gap: '12px',
      flexShrink: 0
    }}>
      {/* Brand & Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
        <div style={{
          width: '32px',
          height: '32px',
          borderRadius: '8px',
          background: 'var(--primary-accent)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          boxShadow: '0 2px 6px var(--primary-accent-glow)'
        }}>
          <Sparkles size={17} color="white" />
        </div>
        <div style={{ minWidth: 0 }}>
          <h1 style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text-main)', letterSpacing: '-0.2px', margin: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            The Lenny Growth Assistant
          </h1>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
            Grounded Podcast RAG & Strategy Copilot
          </span>
        </div>
      </div>

      {/* Right controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
        {/* Corpus badge */}
        <div className="glass-panel hide-sm" style={{
          padding: '5px 10px',
          display: 'flex',
          alignItems: 'center',
          gap: '5px',
          fontSize: '11px',
          color: 'var(--text-muted)',
          background: '#FFFFFF',
          whiteSpace: 'nowrap'
        }}>
          <Database size={12} color="#059669" />
          <span>{config?.sources_count ? `${config.sources_count} Episodes` : '303 Episodes'} · pgvector</span>
        </div>


        <ProviderMenu
          providers={config?.providers}
          activeProvider={activeProvider}
          onProviderChange={onProviderChange}
        />

        {/* New Session Button */}
        <button className="glass-button" onClick={onNewSession} style={{ padding: '6px 12px', whiteSpace: 'nowrap' }}>
          <Plus size={14} />
          <span className="hide-xs">New Session</span>
        </button>
      </div>
    </header>
  );
}
