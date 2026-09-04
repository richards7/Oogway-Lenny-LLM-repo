import React, { useEffect, useRef, useState } from 'react';
import { Check, ChevronDown, Cloud, HardDrive, AlertTriangle } from 'lucide-react';

// Fallback list used until /config responds, so the control never renders empty.
const FALLBACK = [
  { id: 'ollama', label: 'Ollama', model: 'llama3.2:3b', kind: 'local', configured: true },
  { id: 'anthropic', label: 'Anthropic', model: 'claude-3-5-sonnet', kind: 'cloud', configured: false },
  { id: 'openai', label: 'OpenAI', model: 'gpt-4o', kind: 'cloud', configured: false }
];

export default function ProviderMenu({ providers, activeProvider, onProviderChange }) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef(null);

  const list = providers && providers.length ? providers : FALLBACK;
  const active = list.find((p) => p.id === activeProvider) || list[0];

  // Close on outside click or Escape - a popover that traps the page is worse
  // than the native select it replaced.
  useEffect(() => {
    if (!open) return;
    const onDown = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    };
    const onKey = (e) => { if (e.key === 'Escape') setOpen(false); };
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  const select = (id) => {
    onProviderChange(id);
    setOpen(false);
  };

  return (
    <div ref={wrapRef} style={{ position: 'relative', flexShrink: 0 }}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
        title="Change model provider"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '5px 10px',
          background: '#FFFFFF',
          border: `1px solid ${open ? 'var(--primary-accent)' : 'var(--border-subtle)'}`,
          borderRadius: '9px',
          cursor: 'pointer',
          transition: 'border-color 0.15s ease, box-shadow 0.15s ease',
          boxShadow: open ? '0 0 0 3px var(--primary-accent-glow)' : 'none',
          maxWidth: '230px'
        }}
      >
        <StatusDot ok={active?.configured} />
        <span style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', minWidth: 0 }}>
          <span style={{
            fontSize: '12px', fontWeight: 700, color: 'var(--text-main)', lineHeight: 1.25,
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '160px'
          }}>
            {active?.label}
          </span>
          <span style={{
            fontSize: '10px', color: 'var(--text-dim)', lineHeight: 1.25,
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '160px'
          }}>
            {active?.model}
          </span>
        </span>
        <ChevronDown
          size={14}
          color="var(--text-muted)"
          style={{ flexShrink: 0, transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.18s ease' }}
        />
      </button>

      {open && (
        <div
          role="listbox"
          className="provider-menu"
          style={{
            position: 'absolute',
            top: 'calc(100% + 8px)',
            right: 0,
            width: '298px',
            background: '#FFFFFF',
            border: '1px solid var(--border-subtle)',
            borderRadius: '12px',
            boxShadow: '0 12px 32px rgba(31,30,28,0.14)',
            padding: '6px',
            zIndex: 120
          }}
        >
          <div style={{
            padding: '7px 10px 6px',
            fontSize: '10px',
            fontWeight: 700,
            letterSpacing: '0.5px',
            textTransform: 'uppercase',
            color: 'var(--text-dim)'
          }}>
            Model provider
          </div>

          {list.map((p) => {
            const isActive = p.id === activeProvider;
            return (
              <button
                key={p.id}
                role="option"
                aria-selected={isActive}
                onClick={() => select(p.id)}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '9px',
                  padding: '9px 10px',
                  background: isActive ? '#FBF0EB' : 'transparent',
                  border: `1px solid ${isActive ? '#F4C5B5' : 'transparent'}`,
                  borderRadius: '9px',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'background 0.13s ease'
                }}
                onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.background = '#F6F2EC'; }}
                onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.background = 'transparent'; }}
              >
                <span style={{ marginTop: '2px', flexShrink: 0 }}>
                  {p.kind === 'local'
                    ? <HardDrive size={15} color="var(--primary-accent)" />
                    : <Cloud size={15} color="var(--text-muted)" />}
                </span>

                <span style={{ flex: 1, minWidth: 0 }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontSize: '12.5px', fontWeight: 700, color: 'var(--text-main)' }}>
                      {p.label}
                    </span>
                    <span style={{
                      fontSize: '9.5px',
                      fontWeight: 700,
                      letterSpacing: '0.3px',
                      textTransform: 'uppercase',
                      color: p.kind === 'local' ? '#059669' : 'var(--text-muted)',
                      background: p.kind === 'local' ? '#ECFDF5' : '#F1ECE4',
                      border: `1px solid ${p.kind === 'local' ? '#A7F3D0' : '#E2DACE'}`,
                      padding: '1px 5px',
                      borderRadius: '4px'
                    }}>
                      {p.kind}
                    </span>
                  </span>

                  <span style={{
                    display: 'block',
                    fontSize: '11px',
                    color: 'var(--text-muted)',
                    marginTop: '2px',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  }}>
                    {p.model}
                  </span>

                  {/* Say why a provider will not work rather than silently failing later. */}
                  {!p.configured && p.detail && (
                    <span style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      fontSize: '10.5px',
                      color: '#B45309',
                      marginTop: '4px'
                    }}>
                      <AlertTriangle size={11} color="#B45309" style={{ flexShrink: 0 }} />
                      {p.detail}
                    </span>
                  )}
                </span>

                {isActive && <Check size={15} color="var(--primary-accent)" style={{ flexShrink: 0, marginTop: '2px' }} />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

function StatusDot({ ok }) {
  return (
    <span
      title={ok ? 'Ready' : 'Not configured'}
      style={{
        width: '7px',
        height: '7px',
        borderRadius: '50%',
        flexShrink: 0,
        background: ok ? '#10B981' : '#D97706',
        boxShadow: ok ? '0 0 0 3px rgba(16,185,129,0.16)' : '0 0 0 3px rgba(217,119,6,0.16)'
      }}
    />
  );
}
