import React from 'react';
import { Plus, MessageSquare, Trash2, Clock, PanelLeftClose, PanelLeftOpen } from 'lucide-react';

const iconButtonStyle = {
  background: 'none',
  border: 'none',
  color: 'var(--text-muted)',
  cursor: 'pointer',
  padding: '6px',
  borderRadius: '6px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  flexShrink: 0
};

export default function Sidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  width = 260,
  collapsed = false,
  onToggleCollapse,
  onResizeStart,
  onResizeReset
}) {
  // Collapsed: a narrow rail that keeps the re-open control on screen.
  if (collapsed) {
    return (
      <aside style={{
        width: '48px',
        height: '100%',
        background: '#F6F2EC',
        borderRight: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '8px',
        padding: '12px 0',
        zIndex: 5,
        flexShrink: 0
      }}>
        <button
          onClick={onToggleCollapse}
          style={iconButtonStyle}
          title="Show sidebar"
          aria-label="Show sidebar"
          aria-expanded="false"
          onMouseEnter={(e) => { e.currentTarget.style.background = '#EDE6DC'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'none'; }}
        >
          <PanelLeftOpen size={18} />
        </button>

        <button
          onClick={onNewSession}
          style={iconButtonStyle}
          title="New chat"
          aria-label="New chat"
          onMouseEnter={(e) => { e.currentTarget.style.background = '#EDE6DC'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'none'; }}
        >
          <Plus size={18} />
        </button>
      </aside>
    );
  }

  return (
    <aside style={{
      width: `${width}px`,
      height: '100%',
      background: '#F6F2EC',
      borderRight: '1px solid var(--border-subtle)',
      display: 'flex',
      flexDirection: 'column',
      zIndex: 5,
      position: 'relative',
      flexShrink: 0
    }}>
      {/* Sidebar Header */}
      <div style={{
        padding: '16px',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        gap: '8px'
      }}>
        <button
          onClick={onNewSession}
          className="primary-button"
          style={{ flex: 1, minWidth: 0, justifyContent: 'center', padding: '10px 16px' }}
        >
          <Plus size={16} />
          <span>New Chat</span>
        </button>

        <button
          onClick={onToggleCollapse}
          style={iconButtonStyle}
          title="Hide sidebar"
          aria-label="Hide sidebar"
          aria-expanded="true"
          onMouseEnter={(e) => { e.currentTarget.style.background = '#EDE6DC'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'none'; }}
        >
          <PanelLeftClose size={18} />
        </button>
      </div>

      {/* History Section Title */}
      <div style={{
        padding: '12px 16px 6px 16px',
        fontSize: '11px',
        fontWeight: '700',
        color: 'var(--text-muted)',
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
        display: 'flex',
        alignItems: 'center',
        gap: '6px'
      }}>
        <Clock size={12} />
        <span>Chat History</span>
      </div>

      {/* Sessions List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '0 8px 16px 8px' }}>
        {(!Array.isArray(sessions) || sessions.length === 0) ? (
          <div style={{ padding: '16px', fontSize: '12px', color: 'var(--text-dim)', textAlign: 'center' }}>
            No chat history yet. Start a new session above!
          </div>
        ) : (
          sessions.map((s) => {
            const isActive = s.id === activeSessionId;
            return (
              <div
                key={s.id}
                onClick={() => onSelectSession(s.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 12px',
                  margin: '4px 0',
                  borderRadius: '8px',
                  background: isActive ? '#F2EBE1' : 'transparent',
                  border: isActive ? '1px solid var(--border-active)' : '1px solid transparent',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
                onMouseEnter={(e) => {
                  if (!isActive) e.currentTarget.style.background = '#EDE6DC';
                }}
                onMouseLeave={(e) => {
                  if (!isActive) e.currentTarget.style.background = 'transparent';
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden', flex: 1 }}>
                  <MessageSquare size={14} color={isActive ? 'var(--primary-accent)' : 'var(--text-muted)'} style={{ flexShrink: 0 }} />
                  <span style={{
                    fontSize: '13px',
                    fontWeight: isActive ? '700' : '500',
                    color: isActive ? 'var(--text-main)' : 'var(--text-muted)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  }}>
                    {s.title || "New Chat Session"}
                  </span>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(s.id);
                  }}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--text-dim)',
                    cursor: 'pointer',
                    padding: '2px',
                    borderRadius: '4px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginLeft: '6px'
                  }}
                  title="Delete chat session"
                  onMouseEnter={(e) => e.currentTarget.style.color = '#DC2626'}
                  onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-dim)'}
                >
                  <Trash2 size={13} />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Drag handle - double-click resets to the default width */}
      <div
        onPointerDown={onResizeStart}
        onDoubleClick={onResizeReset}
        role="separator"
        aria-orientation="vertical"
        aria-label="Resize sidebar"
        title="Drag to resize (double-click to reset)"
        style={{
          position: 'absolute',
          top: 0,
          right: '-3px',
          width: '6px',
          height: '100%',
          cursor: 'col-resize',
          zIndex: 10,
          touchAction: 'none'
        }}
        onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--primary-accent)'; e.currentTarget.style.opacity = '0.35'; }}
        onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
      />
    </aside>
  );
}
