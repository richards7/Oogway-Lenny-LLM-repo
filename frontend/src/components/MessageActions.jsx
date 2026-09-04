import React, { useState } from 'react';
import { Copy, Check, Pencil, RefreshCw } from 'lucide-react';

const actionStyle = {
  background: 'none',
  border: 'none',
  color: 'var(--text-dim)',
  cursor: 'pointer',
  padding: '4px 6px',
  borderRadius: '5px',
  display: 'inline-flex',
  alignItems: 'center',
  gap: '4px',
  fontSize: '11px',
  fontWeight: 600,
  lineHeight: 1,
  transition: 'background 0.15s ease, color 0.15s ease'
};

const hoverIn = (e) => {
  e.currentTarget.style.background = '#EDE6DC';
  e.currentTarget.style.color = 'var(--text-main)';
};
const hoverOut = (e) => {
  e.currentTarget.style.background = 'none';
  e.currentTarget.style.color = 'var(--text-dim)';
};

/**
 * Hover action row beneath a message. Copy is offered on every message;
 * edit belongs to the user's own turns and regenerate to the assistant's.
 */
export default function MessageActions({ content, isUser, onEdit, onRegenerate, disabled }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content || '');
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* clipboard blocked (insecure origin / denied permission) - stay silent */
    }
  };

  return (
    <div
      className="message-actions"
      style={{
        display: 'flex',
        gap: '2px',
        marginTop: '6px',
        justifyContent: isUser ? 'flex-end' : 'flex-start'
      }}
    >
      <button
        style={actionStyle}
        onClick={handleCopy}
        title="Copy message"
        aria-label="Copy message"
        onMouseEnter={hoverIn}
        onMouseLeave={hoverOut}
      >
        {copied ? <Check size={12} color="#059669" /> : <Copy size={12} />}
        <span style={copied ? { color: '#059669' } : undefined}>{copied ? 'Copied' : 'Copy'}</span>
      </button>

      {isUser && onEdit && (
        <button
          style={actionStyle}
          onClick={onEdit}
          disabled={disabled}
          title="Edit and resend"
          aria-label="Edit message"
          onMouseEnter={hoverIn}
          onMouseLeave={hoverOut}
        >
          <Pencil size={12} />
          <span>Edit</span>
        </button>
      )}

      {!isUser && onRegenerate && (
        <button
          style={actionStyle}
          onClick={onRegenerate}
          disabled={disabled}
          title="Regenerate this response"
          aria-label="Regenerate response"
          onMouseEnter={hoverIn}
          onMouseLeave={hoverOut}
        >
          <RefreshCw size={12} />
          <span>Retry</span>
        </button>
      )}
    </div>
  );
}
