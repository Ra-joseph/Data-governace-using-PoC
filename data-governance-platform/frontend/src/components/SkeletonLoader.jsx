// frontend/src/components/SkeletonLoader.jsx
import React from 'react';

/**
 * Reusable skeleton loader component.
 * Uses the .skeleton class from App.css (shimmer animation already defined).
 *
 * Props:
 *   type: 'card' | 'row' | 'stat' | 'chart' | 'text' (default: 'text')
 *   count: number of items to render (default: 1)
 */
export function SkeletonLoader({ type = 'text', count = 1 }) {
  const items = Array.from({ length: count }, (_, i) => i);

  if (type === 'stat') {
    return (
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
        gap: '1rem',
      }}>
        {items.map(i => (
          <div key={i} style={{
            background: 'var(--color-bg-secondary)',
            border: '1px solid var(--color-border-default)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.5rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}>
            <div className="skeleton" style={{ width: 40, height: 40, borderRadius: 'var(--radius-md)' }} />
            <div className="skeleton" style={{ height: 28, width: '60%', borderRadius: 'var(--radius-sm)' }} />
            <div className="skeleton" style={{ height: 14, width: '40%', borderRadius: 'var(--radius-sm)' }} />
          </div>
        ))}
      </div>
    );
  }

  if (type === 'card') {
    return (
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
        gap: '1rem',
      }}>
        {items.map(i => (
          <div key={i} style={{
            background: 'var(--color-bg-secondary)',
            border: '1px solid var(--color-border-default)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.5rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div className="skeleton" style={{ width: 36, height: 36, borderRadius: 'var(--radius-md)', flexShrink: 0 }} />
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
                <div className="skeleton" style={{ height: 16, width: '70%', borderRadius: 'var(--radius-sm)' }} />
                <div className="skeleton" style={{ height: 12, width: '40%', borderRadius: 'var(--radius-sm)' }} />
              </div>
            </div>
            <div className="skeleton" style={{ height: 14, width: '100%', borderRadius: 'var(--radius-sm)' }} />
            <div className="skeleton" style={{ height: 14, width: '80%', borderRadius: 'var(--radius-sm)' }} />
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.25rem' }}>
              <div className="skeleton" style={{ height: 22, width: 64, borderRadius: 9999 }} />
              <div className="skeleton" style={{ height: 22, width: 80, borderRadius: 9999 }} />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (type === 'row') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {items.map(i => (
          <div key={i} style={{
            background: 'var(--color-bg-secondary)',
            border: '1px solid var(--color-border-default)',
            borderRadius: 'var(--radius-md)',
            padding: '1rem 1.25rem',
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
          }}>
            <div className="skeleton" style={{ width: 32, height: 32, borderRadius: 'var(--radius-md)', flexShrink: 0 }} />
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
              <div className="skeleton" style={{ height: 14, width: '50%', borderRadius: 'var(--radius-sm)' }} />
              <div className="skeleton" style={{ height: 12, width: '30%', borderRadius: 'var(--radius-sm)' }} />
            </div>
            <div className="skeleton" style={{ height: 22, width: 70, borderRadius: 9999 }} />
          </div>
        ))}
      </div>
    );
  }

  if (type === 'chart') {
    return (
      <div style={{
        background: 'var(--color-bg-secondary)',
        border: '1px solid var(--color-border-default)',
        borderRadius: 'var(--radius-lg)',
        padding: '1.5rem',
      }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1rem' }}>
          <div className="skeleton" style={{ height: 18, width: '30%', borderRadius: 'var(--radius-sm)' }} />
          <div className="skeleton" style={{ height: 12, width: '20%', borderRadius: 'var(--radius-sm)' }} />
        </div>
        <div className="skeleton" style={{ height: 220, width: '100%', borderRadius: 'var(--radius-md)' }} />
      </div>
    );
  }

  // Default: 'text'
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      {items.map(i => (
        <div key={i} className="skeleton" style={{ height: 14, width: `${80 - (i * 10)}%`, borderRadius: 'var(--radius-sm)' }} />
      ))}
    </div>
  );
}
