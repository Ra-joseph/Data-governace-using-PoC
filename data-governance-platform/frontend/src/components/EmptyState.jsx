// frontend/src/components/EmptyState.jsx
import React from 'react';
import { Inbox } from 'lucide-react';

/**
 * Reusable empty state component.
 *
 * Props:
 *   icon: Lucide icon component (default: Inbox)
 *   title: string — headline (required)
 *   description: string — body text (optional)
 *   actionLabel: string — CTA button text (optional)
 *   onAction: function — CTA button handler (optional)
 */
export function EmptyState({ icon: Icon = Inbox, title, description, actionLabel, onAction }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      textAlign: 'center',
      padding: '4rem 2rem',
      color: 'var(--color-text-secondary)',
    }}>
      <div style={{
        width: 64,
        height: 64,
        background: 'var(--color-bg-tertiary)',
        border: '1px solid var(--color-border-default)',
        borderRadius: 'var(--radius-lg)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: '1.25rem',
        color: 'var(--color-text-tertiary)',
      }}>
        <Icon size={28} strokeWidth={1.5} />
      </div>
      <h3 style={{
        fontFamily: 'var(--font-display)',
        fontSize: '1.125rem',
        fontWeight: 600,
        color: 'var(--color-text-primary)',
        marginBottom: '0.5rem',
      }}>
        {title}
      </h3>
      {description && (
        <p style={{
          fontSize: '0.9375rem',
          color: 'var(--color-text-secondary)',
          lineHeight: 1.6,
          maxWidth: 380,
          marginBottom: actionLabel ? '1.5rem' : 0,
        }}>
          {description}
        </p>
      )}
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.625rem 1.5rem',
            background: 'var(--color-accent-primary)',
            color: '#fff',
            border: 'none',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.9375rem',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all var(--transition-base)',
          }}
          onMouseEnter={e => e.currentTarget.style.background = 'var(--color-accent-secondary)'}
          onMouseLeave={e => e.currentTarget.style.background = 'var(--color-accent-primary)'}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
