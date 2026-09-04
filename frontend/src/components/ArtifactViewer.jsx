import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Eye, Code, Copy, Check, ShieldCheck, X, Sparkles,
  Download, Maximize2, Minimize2
} from 'lucide-react';

const iconButtonStyle = {
  background: 'none',
  border: 'none',
  color: 'var(--text-muted)',
  cursor: 'pointer',
  padding: '5px',
  borderRadius: '6px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  flexShrink: 0,
  transition: 'background 0.15s ease, color 0.15s ease'
};

const hoverIn = (e) => { e.currentTarget.style.background = '#EAE4DA'; };
const hoverOut = (e) => { e.currentTarget.style.background = 'none'; };

export default function ArtifactViewer({ artifact, onClose, width = 460, onResizeStart, onResizeReset }) {
  const [viewMode, setViewMode] = useState('rendered'); // 'rendered' | 'source'
  const [copied, setCopied] = useState(false);
  const [maximized, setMaximized] = useState(false);

  // Reset the view whenever a different artifact is opened.
  useEffect(() => {
    setViewMode('rendered');
    setCopied(false);
  }, [artifact?.id]);

  // Escape closes the expanded overlay first, then the panel.
  useEffect(() => {
    const onKey = (e) => {
      if (e.key !== 'Escape') return;
      if (maximized) setMaximized(false);
      else onClose?.();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [maximized, onClose]);

  if (!artifact) return null;

  const isHtml = artifact.type === 'html';
  const artifactType = (artifact.type || 'Artifact').toUpperCase();

  const handleCopy = () => {
    navigator.clipboard.writeText(artifact.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([artifact.content], {
      type: isHtml ? 'text/html;charset=utf-8' : 'text/markdown;charset=utf-8'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `lenny-artifact-${(artifact.id || 'draft').toString().slice(0, 8)}.${isHtml ? 'html' : 'md'}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const panelStyle = maximized
    ? {
        position: 'fixed',
        top: '24px',
        left: '24px',
        right: '24px',
        bottom: '24px',
        borderRadius: '14px',
        border: '1px solid var(--border-subtle)',
        boxShadow: '0 24px 60px rgba(31, 30, 28, 0.22)',
        zIndex: 200
      }
    : {
        width: `${width}px`,
        height: '100%',
        borderLeft: '1px solid var(--border-subtle)',
        boxShadow: '-4px 0 20px rgba(31, 30, 28, 0.04)',
        position: 'relative',
        zIndex: 10
      };

  return (
    <>
      {maximized && (
        <div
          onClick={() => setMaximized(false)}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(31, 30, 28, 0.34)',
            backdropFilter: 'blur(2px)',
            zIndex: 199
          }}
        />
      )}

      <div className={maximized ? '' : 'artifact-panel'} style={{
        background: '#FAF8F5',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        ...panelStyle
      }}>
        {/* Canvas Top Bar. The left group truncates; the action group never shrinks,
            which is what keeps the close button on screen at narrow widths. */}
        <div style={{
          padding: '10px 14px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '10px',
          background: '#F6F1E8',
          flexShrink: 0
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            minWidth: 0,
            flex: '1 1 auto',
            overflow: 'hidden'
          }}>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              fontSize: '11px',
              fontWeight: '700',
              background: '#FBF0EB',
              color: '#C56546',
              padding: '3px 9px',
              borderRadius: '6px',
              border: '1px solid #F4C5B5',
              letterSpacing: '0.4px',
              whiteSpace: 'nowrap',
              flexShrink: 0
            }}>
              <Sparkles size={12} color="#D97757" />
              <span>{artifactType}</span>
            </div>

            {artifact.sanitized && (
              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '11px',
                color: '#059669',
                fontWeight: '600',
                background: '#ECFDF5',
                border: '1px solid #A7F3D0',
                padding: '2px 8px',
                borderRadius: '6px',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                minWidth: 0
              }}>
                <ShieldCheck size={13} color="#059669" style={{ flexShrink: 0 }} />
                <span>Sanitized</span>
              </div>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
            {/* View Mode Toggle Pill */}
            <div style={{
              padding: '2px',
              display: 'flex',
              gap: '2px',
              background: '#EAE4DA',
              borderRadius: '7px',
              border: '1px solid #DFD9CF'
            }}>
              {[
                { mode: 'rendered', Icon: Eye, label: 'Preview' },
                { mode: 'source', Icon: Code, label: 'Source' }
              ].map(({ mode, Icon, label }) => (
                <button
                  key={mode}
                  onClick={() => setViewMode(mode)}
                  title={label}
                  style={{
                    background: viewMode === mode ? '#FFFFFF' : 'transparent',
                    color: viewMode === mode ? 'var(--text-main)' : 'var(--text-muted)',
                    border: 'none',
                    padding: '4px 9px',
                    borderRadius: '5px',
                    fontSize: '11px',
                    fontWeight: '600',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    whiteSpace: 'nowrap',
                    boxShadow: viewMode === mode ? '0 1px 3px rgba(0,0,0,0.06)' : 'none',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <Icon size={12} />
                  <span>{label}</span>
                </button>
              ))}
            </div>

            <button
              style={iconButtonStyle}
              onClick={handleCopy}
              title={copied ? 'Copied' : 'Copy content'}
              aria-label="Copy content"
              onMouseEnter={hoverIn}
              onMouseLeave={hoverOut}
            >
              {copied ? <Check size={15} color="#059669" /> : <Copy size={15} />}
            </button>

            <button
              style={iconButtonStyle}
              onClick={handleDownload}
              title={`Download .${isHtml ? 'html' : 'md'}`}
              aria-label="Download artifact"
              onMouseEnter={hoverIn}
              onMouseLeave={hoverOut}
            >
              <Download size={15} />
            </button>

            <button
              style={iconButtonStyle}
              onClick={() => setMaximized((m) => !m)}
              title={maximized ? 'Exit full view (Esc)' : 'Expand'}
              aria-label={maximized ? 'Exit full view' : 'Expand'}
              onMouseEnter={hoverIn}
              onMouseLeave={hoverOut}
            >
              {maximized ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
            </button>

            <button
              style={iconButtonStyle}
              onClick={onClose}
              title="Close canvas (Esc)"
              aria-label="Close canvas"
              onMouseEnter={(e) => { e.currentTarget.style.background = '#F6DEDE'; e.currentTarget.style.color = '#B91C1C'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'none'; e.currentTarget.style.color = 'var(--text-muted)'; }}
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Canvas Paper Workspace */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          overflowX: 'hidden',
          padding: maximized ? '28px' : '18px',
          background: '#FAF8F5',
          display: 'flex',
          flexDirection: 'column'
        }}>
          {viewMode === 'source' ? (
            <pre style={{
              fontSize: '12.5px',
              fontFamily: 'var(--font-mono)',
              color: '#9C4221',
              background: '#F6F1E8',
              border: '1px solid #E8E0D4',
              padding: '18px',
              borderRadius: '10px',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              lineHeight: '1.7',
              tabSize: 2,
              margin: 0
            }}>
              {artifact.content}
            </pre>
          ) : isHtml ? (
            /* Sandboxed iframe deliberately omitting allow-scripts */
            <iframe
              title="Artifact Canvas Render"
              srcDoc={artifact.content}
              sandbox="allow-forms"
              style={{
                width: '100%',
                flex: 1,
                minHeight: maximized ? '100%' : '480px',
                border: '1px solid var(--border-subtle)',
                background: '#FFFFFF',
                borderRadius: '10px',
                boxShadow: '0 2px 12px rgba(31, 30, 28, 0.04)'
              }}
            />
          ) : (
            <div style={{
              background: '#FFFFFF',
              padding: maximized ? '48px 56px' : '32px 34px',
              borderRadius: '10px',
              border: '1px solid var(--border-subtle)',
              boxShadow: '0 2px 12px rgba(31, 30, 28, 0.04)',
              minHeight: '100%',
              width: '100%',
              maxWidth: '820px',
              margin: '0 auto'
            }}>
              {/* Wider measure + looser rhythm than a chat bubble: this is a document. */}
              <div className="markdown-body artifact-prose">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {artifact.content}
                </ReactMarkdown>
              </div>
            </div>
          )}
        </div>

        {/* Drag handle - double-click resets to the default width */}
        {!maximized && (
          <div
            onPointerDown={onResizeStart}
            onDoubleClick={onResizeReset}
            role="separator"
            aria-orientation="vertical"
            aria-label="Resize artifact panel"
            title="Drag to resize (double-click to reset)"
            style={{
              position: 'absolute',
              top: 0,
              left: '-3px',
              width: '6px',
              height: '100%',
              cursor: 'col-resize',
              zIndex: 20,
              touchAction: 'none'
            }}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--primary-accent)'; e.currentTarget.style.opacity = '0.35'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
          />
        )}
      </div>
    </>
  );
}
