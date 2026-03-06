// frontend/src/components/ErrorBoundary.jsx
import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

/**
 * React error boundary component.
 * Catches unhandled JS errors in the render tree and shows a friendly recovery UI.
 */
export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('ErrorBoundary caught an error:', error, info);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          padding: '2rem',
          background: 'var(--color-bg-primary)',
        }}>
          <div style={{
            background: 'var(--color-bg-secondary)',
            border: '1px solid var(--color-border-default)',
            borderRadius: 'var(--radius-xl)',
            padding: '3rem 2.5rem',
            maxWidth: 480,
            width: '100%',
            textAlign: 'center',
            boxShadow: 'var(--shadow-lg)',
          }}>
            <div style={{
              width: 64,
              height: 64,
              background: 'rgba(220, 38, 38, 0.1)',
              borderRadius: 'var(--radius-lg)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1.5rem',
              color: 'var(--color-error)',
            }}>
              <AlertTriangle size={32} />
            </div>
            <h2 style={{
              fontFamily: 'var(--font-display)',
              fontSize: '1.5rem',
              fontWeight: 700,
              color: 'var(--color-text-primary)',
              marginBottom: '0.75rem',
            }}>
              Something went wrong
            </h2>
            <p style={{
              color: 'var(--color-text-secondary)',
              lineHeight: 1.6,
              marginBottom: '2rem',
            }}>
              An unexpected error occurred. Refreshing the page usually resolves this.
            </p>
            {this.state.error && (
              <details style={{
                textAlign: 'left',
                background: 'var(--color-bg-tertiary)',
                border: '1px solid var(--color-border-default)',
                borderRadius: 'var(--radius-md)',
                padding: '0.75rem 1rem',
                marginBottom: '1.5rem',
                fontSize: '0.8125rem',
                fontFamily: 'var(--font-mono)',
                color: 'var(--color-text-tertiary)',
              }}>
                <summary style={{ cursor: 'pointer', color: 'var(--color-text-secondary)', marginBottom: '0.5rem' }}>
                  Error details
                </summary>
                {this.state.error.message}
              </details>
            )}
            <button
              onClick={this.handleReset}
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
            >
              <RefreshCw size={16} />
              Refresh page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
