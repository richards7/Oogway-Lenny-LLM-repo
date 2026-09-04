import React, { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, FileText, X } from 'lucide-react';
import AssistantAvatar from './AssistantAvatar';
import ThinkingIndicator from './ThinkingIndicator';
import MessageActions from './MessageActions';

// Map internal provider names to clean display labels
const PROVIDER_LABELS = {
  ollama: '🦙 Lenny AI (Local)',
  anthropic: '✦ Lenny AI (Anthropic)',
  openai: '✦ Lenny AI (OpenAI)',
  user: 'You',
};

function getProviderLabel(provider) {
  if (!provider || provider === 'user') return 'You';
  return PROVIDER_LABELS[provider.toLowerCase()] || `✦ Lenny AI (${provider})`;
}

export default function ChatWindow({
  messages,
  isLoading,
  onSelectArtifact,
  activeArtifactId = null,
  onEditMessage,
  onRegenerate
}) {
  const [activeCitation, setActiveCitation] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editDraft, setEditDraft] = useState('');

  const beginEdit = (msg) => {
    setEditingId(msg.id);
    setEditDraft(msg.content);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditDraft('');
  };

  const submitEdit = (msg) => {
    const next = editDraft.trim();
    if (!next || next === msg.content) return cancelEdit();
    cancelEdit();
    onEditMessage?.(msg.id, next);
  };
  const bottomRef = useRef(null);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div style={{
      flex: 1,
      overflowY: 'auto',
      padding: '24px 20px',
      display: 'flex',
      flexDirection: 'column',
      gap: '20px'
    }}>
      {messages.length === 0 && (
        <div style={{
          margin: 'auto',
          textAlign: 'center',
          maxWidth: '480px',
          padding: '0 16px',
          color: 'var(--text-muted)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '16px' }}>
            <AssistantAvatar size={52} />
          </div>
          <h2 style={{ color: 'var(--text-main)', fontSize: '19px', fontWeight: '700', marginBottom: '8px', letterSpacing: '-0.3px' }}>
            Lenny Growth Strategy Assistant
          </h2>
          <p style={{ fontSize: '13px', lineHeight: '1.65', color: 'var(--text-muted)' }}>
            Ask strategic product &amp; growth questions grounded in Lenny's Podcast transcripts. Generate Ship 30/30 essays and visual HTML artifacts.
          </p>
        </div>
      )}

      {messages.map((msg, index) => {
        const isEditing = editingId === msg.id;
        const isPending = typeof msg.id === 'string' && msg.id.startsWith('temp-');
        return (
        <div
          key={msg.id || index}
          style={{
            display: 'flex',
            gap: '12px',
            alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: msg.role === 'user' ? 'min(80%, 640px)' : 'min(90%, 760px)',
            width: '100%'
          }}
        >
          {msg.role !== 'user' && <AssistantAvatar size={32} />}

          <div className="message-row" style={{ flex: 1, minWidth: 0 }}>
            {/* Bubble */}
            <div 
              style={{
                padding: '16px 20px',
                borderRadius: '12px',
                background: msg.role === 'user' 
                  ? 'var(--bg-user-bubble)' 
                  : 'var(--bg-surface)',
                border: msg.role === 'user' 
                  ? '1px solid #E5DDD0' 
                  : '1px solid var(--border-subtle)',
                boxShadow: msg.role === 'user'
                  ? 'none'
                  : '0 1px 3px rgba(31, 30, 28, 0.04), 0 4px 12px rgba(31, 30, 28, 0.02)'
              }}
            >
              {/* Message Header info */}
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center', 
                marginBottom: '8px',
                fontSize: '11px',
                color: 'var(--text-dim)'
              }}>
                <span style={{ fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.4px', color: 'var(--text-muted)' }}>
                  {msg.role === 'user' ? 'You' : getProviderLabel(msg.model_provider)}
                </span>
                {msg.artifact && (() => {
                  // Rendered for every message that produced an artifact, and it stays
                  // put when the panel is closed - only the open/closed styling changes.
                  const isOpen = activeArtifactId && msg.artifact.id === activeArtifactId;
                  return (
                    <button
                      className="glass-button"
                      style={{
                        padding: '3px 9px',
                        fontSize: '11px',
                        background: isOpen ? '#FBF0EB' : '#F6F0E6',
                        borderColor: isOpen ? 'var(--primary-accent)' : '#E8D8C4',
                        color: isOpen ? '#C56546' : 'inherit',
                        fontWeight: isOpen ? '700' : '600'
                      }}
                      onClick={() => onSelectArtifact(msg.artifact)}
                      title={isOpen ? 'Showing in the canvas' : 'Open in the artifact canvas'}
                    >
                      <FileText size={12} color="var(--primary-accent)" />
                      <span>{isOpen ? 'Viewing' : 'View Artifact'}</span>
                    </button>
                  );
                })()}
              </div>

              {/* Message Body */}
              {isEditing ? (
                <div>
                  <textarea
                    value={editDraft}
                    onChange={(e) => setEditDraft(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submitEdit(msg); }
                      if (e.key === 'Escape') { e.preventDefault(); cancelEdit(); }
                    }}
                    autoFocus
                    rows={Math.min(10, Math.max(2, editDraft.split('\n').length + 1))}
                    style={{
                      width: '100%',
                      resize: 'vertical',
                      fontFamily: 'inherit',
                      fontSize: '14px',
                      lineHeight: '1.6',
                      color: 'var(--text-main)',
                      background: '#FFFFFF',
                      border: '1px solid var(--border-active)',
                      borderRadius: '8px',
                      padding: '10px 12px',
                      outline: 'none'
                    }}
                  />
                  <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', marginTop: '8px' }}>
                    <button className="glass-button" style={{ padding: '4px 12px', fontSize: '12px' }} onClick={cancelEdit}>
                      Cancel
                    </button>
                    <button
                      className="primary-button"
                      style={{ padding: '5px 14px', fontSize: '12px' }}
                      onClick={() => submitEdit(msg)}
                      disabled={!editDraft.trim()}
                    >
                      Save &amp; submit
                    </button>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '6px', textAlign: 'right' }}>
                    Editing replaces every reply after this message.
                  </div>
                </div>
              ) : (
                <div className="markdown-body">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {msg.content}
                  </ReactMarkdown>
                </div>
              )}

              {/* Citations Footer */}
              {msg.citations && msg.citations.length > 0 && (
                <div style={{
                  marginTop: '14px',
                  paddingTop: '12px',
                  borderTop: '1px solid var(--border-subtle)'
                }}>
                  <div style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.4px' }}>
                    Transcript Sources ({msg.citations.length}):
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {msg.citations.map((cit, cIdx) => (
                      <span 
                        key={cIdx} 
                        className="citation-chip"
                        onClick={() => setActiveCitation(cit)}
                      >
                        [Source {cIdx + 1}: {cit.title} (chunk {cit.position})]
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {!isEditing && !isPending && (
              <MessageActions
                content={msg.content}
                isUser={msg.role === 'user'}
                disabled={isLoading}
                onEdit={msg.role === 'user' ? () => beginEdit(msg) : undefined}
                onRegenerate={msg.role !== 'user' ? () => onRegenerate?.(msg.id) : undefined}
              />
            )}
          </div>

          {msg.role === 'user' && (
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: '#EAE4DA',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}>
              <User size={16} color="var(--text-main)" />
            </div>
          )}
        </div>
        );
      })}

      {isLoading && <ThinkingIndicator />}

      {/* Auto-scroll anchor */}
      <div ref={bottomRef} style={{ height: 0 }} />

      {/* Citation Detail Modal */}
      {activeCitation && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(31, 30, 28, 0.4)',
          backdropFilter: 'blur(3px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100
        }}>
          <div className="glass-panel" style={{
            width: '500px',
            maxWidth: '90%',
            padding: '24px',
            background: '#FFFFFF',
            border: '1px solid var(--border-subtle)',
            boxShadow: '0 8px 30px rgba(31, 30, 28, 0.12)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h3 style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text-main)' }}>
                {activeCitation.title}
              </h3>
              <button 
                onClick={() => setActiveCitation(null)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <X size={18} />
              </button>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '12px' }}>
              Chunk Position: #{activeCitation.position} | Similarity Score: {(activeCitation.score * 100).toFixed(1)}%
            </div>
            <div style={{
              background: '#F6F1E8',
              border: '1px solid #E8E0D4',
              padding: '14px',
              borderRadius: '8px',
              fontSize: '13px',
              lineHeight: '1.6',
              color: 'var(--text-main)',
              maxHeight: '220px',
              overflowY: 'auto'
            }}>
              "{activeCitation.snippet}"
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

