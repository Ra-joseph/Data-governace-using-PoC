// frontend/src/components/CopyButton.jsx
import { useState } from 'react';
import { Copy, Check } from 'lucide-react';

/**
 * Copy-to-clipboard button.
 * Displays a clipboard icon that switches to a checkmark for 1.5s after copying.
 *
 * Props:
 *   value: string — the value to copy
 *   label: string — optional tooltip/aria-label (default: 'Copy')
 */
export function CopyButton({ value, label = 'Copy' }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (e) => {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Fallback for older browsers
      const el = document.createElement('textarea');
      el.value = value;
      document.body.appendChild(el);
      el.select();
      document.execCommand('copy');
      document.body.removeChild(el);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  };

  return (
    <button
      onClick={handleCopy}
      title={copied ? 'Copied!' : label}
      aria-label={copied ? 'Copied!' : label}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: 28,
        height: 28,
        padding: 0,
        background: copied ? 'rgba(22, 163, 74, 0.1)' : 'var(--color-bg-tertiary)',
        border: `1px solid ${copied ? 'rgba(22, 163, 74, 0.3)' : 'var(--color-border-default)'}`,
        borderRadius: 'var(--radius-sm)',
        color: copied ? 'var(--color-success)' : 'var(--color-text-tertiary)',
        cursor: 'pointer',
        transition: 'all var(--transition-fast)',
        flexShrink: 0,
      }}
      onMouseEnter={e => {
        if (!copied) {
          e.currentTarget.style.background = 'var(--color-bg-elevated)';
          e.currentTarget.style.color = 'var(--color-text-secondary)';
        }
      }}
      onMouseLeave={e => {
        if (!copied) {
          e.currentTarget.style.background = 'var(--color-bg-tertiary)';
          e.currentTarget.style.color = 'var(--color-text-tertiary)';
        }
      }}
    >
      {copied ? <Check size={14} /> : <Copy size={14} />}
    </button>
  );
}
