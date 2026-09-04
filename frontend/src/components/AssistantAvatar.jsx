import React from 'react';

/**
 * Brand mark for the assistant: an audio waveform that rises left-to-right -
 * podcast source material plus a growth curve, rather than a stock robot glyph.
 * When `thinking` is set the bars animate like an equaliser.
 */
export default function AssistantAvatar({ size = 32, thinking = false }) {
  // Waveform bar geometry: x offset, baseline height. Heights rise then taper,
  // so the mark reads as a signal rather than a flat bar chart.
  const bars = [
    { x: 4.5, h: 7 },
    { x: 8.5, h: 12 },
    { x: 12.5, h: 18 },
    { x: 16.5, h: 12 },
    { x: 20.5, h: 8 }
  ];

  return (
    <div
      className={thinking ? 'assistant-avatar is-thinking' : 'assistant-avatar'}
      style={{
        width: `${size}px`,
        height: `${size}px`,
        borderRadius: `${Math.round(size * 0.28)}px`,
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(145deg, #E08A66 0%, var(--primary-accent) 55%, #B84F31 100%)',
        boxShadow: '0 1px 3px rgba(31,30,28,0.16), inset 0 1px 0 rgba(255,255,255,0.22)'
      }}
      aria-hidden="true"
    >
      <svg
        width={size * 0.72}
        height={size * 0.72}
        viewBox="0 0 28 28"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {bars.map((b, i) => (
          <rect
            key={i}
            className="wave-bar"
            style={{ animationDelay: `${i * 0.11}s` }}
            x={b.x}
            y={14 - b.h / 2}
            width="3"
            height={b.h}
            rx="1.5"
            fill="#FFFFFF"
            opacity={i === 2 ? 1 : 0.82}
          />
        ))}
      </svg>
    </div>
  );
}
