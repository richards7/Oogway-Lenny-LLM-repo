import React, { useState } from 'react';
import { Send, Feather, Code, MessageSquare } from 'lucide-react';

export default function MessageInput({ onSendMessage, disabled }) {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || disabled) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const suggestions = [
    {
      label: "Standard RAG: PLG & Activation",
      prompt: "What is Product-Led Growth (PLG) according to Elena Verna, and how should PMs define activation metrics?",
      icon: MessageSquare
    },
    {
      label: "Ship 30/30 Essay: Founder Mode",
      prompt: "Write a Ship 30/30 essay on Founder Mode based on Brian Chesky's transcript.",
      icon: Feather
    },
    {
      label: "Visual Artifact: Empowered Teams",
      prompt: "Create an HTML visual comparison table component comparing Empowered Product Teams vs Feature Factories based on Marty Cagan's transcript.",
      icon: Code
    }
  ];

  return (
    <div style={{ padding: '0 16px 20px 16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {/* Suggestion Pills */}
      <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '2px', scrollbarWidth: 'none' }}>
        {suggestions.map((s, idx) => {
          const Icon = s.icon;
          return (
            <button
              key={idx}
              className="glass-button"
              style={{ padding: '5px 12px', fontSize: '12px', whiteSpace: 'nowrap', background: '#F4EFE6', borderColor: '#E8E2D8' }}
              onClick={() => onSendMessage(s.prompt)}
              disabled={disabled}
            >
              <Icon size={13} color="var(--primary-accent)" />
              <span>{s.label}</span>
            </button>
          );
        })}
      </div>

      {/* Main Input Form */}
      <form onSubmit={handleSubmit} style={{ position: 'relative' }}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a product/growth question, or request a Ship 30/30 essay or HTML artifact..."
          rows={2}
          disabled={disabled}
          style={{
            width: '100%',
            background: '#FFFFFF',
            border: '1px solid var(--border-subtle)',
            borderRadius: '12px',
            padding: '14px 54px 14px 18px',
            color: 'var(--text-main)',
            fontSize: '14px',
            fontFamily: 'var(--font-sans)',
            resize: 'none',
            outline: 'none',
            lineHeight: '1.5',
            boxShadow: '0 2px 8px rgba(31, 30, 28, 0.04)'
          }}
        />
        <button
          type="submit"
          disabled={!input.trim() || disabled}
          className="primary-button"
          style={{
            position: 'absolute',
            right: '12px',
            bottom: '16px',
            padding: '8px 10px',
            borderRadius: '8px',
            opacity: (!input.trim() || disabled) ? 0.4 : 1
          }}
        >
          <Send size={15} />
        </button>
      </form>
    </div>
  );
}

