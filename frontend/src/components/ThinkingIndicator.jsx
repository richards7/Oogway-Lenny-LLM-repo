import React, { useEffect, useState } from 'react';
import AssistantAvatar from './AssistantAvatar';

// Roughly tracks the real pipeline: retrieve -> rank -> route -> ground -> compose.
// Ordered rather than random so it reads as progress, not decoration.
const PHASES = [
  'Searching transcripts',
  'Ranking passages',
  'Cross-referencing episodes',
  'Routing to a skill',
  'Grounding the answer',
  'Composing'
];

const PHASE_MS = 1900;

export default function ThinkingIndicator() {
  const [phase, setPhase] = useState(0);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    // Hold on the final phase instead of looping back to "Searching" - looping
    // would imply the request restarted.
    const id = setInterval(() => {
      setPhase((p) => (p < PHASES.length - 1 ? p + 1 : p));
    }, PHASE_MS);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const id = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div style={{ display: 'flex', gap: '12px', alignSelf: 'flex-start', alignItems: 'flex-start' }}>
      <AssistantAvatar size={32} thinking />

      <div
        className="glass-panel"
        style={{
          padding: '12px 18px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          minHeight: '44px'
        }}
        role="status"
        aria-live="polite"
      >
        <span
          key={phase}
          className="thinking-phase"
          style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: 500 }}
        >
          {PHASES[phase]}
        </span>

        <div className="typing-dots">
          <span></span><span></span><span></span>
        </div>

        {/* Surfaced only once the wait is long enough to be worth acknowledging. */}
        {elapsed >= 5 && (
          <span style={{ fontSize: '11px', color: 'var(--text-dim)', fontVariantNumeric: 'tabular-nums' }}>
            {elapsed}s
          </span>
        )}
      </div>
    </div>
  );
}
