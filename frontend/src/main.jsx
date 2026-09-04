import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Uncaught application error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          height: '100vh',
          width: '100vw',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#FAF8F5',
          color: '#1F1E1C',
          padding: '24px',
          fontFamily: 'sans-serif',
          textAlign: 'center'
        }}>
          <div style={{
            background: '#FFFFFF',
            border: '1px solid #E8E2D8',
            borderRadius: '12px',
            padding: '32px',
            maxWidth: '480px',
            boxShadow: '0 4px 20px rgba(31,30,28,0.06)'
          }}>
            <h2 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '12px', color: '#D97757' }}>
              Something went wrong
            </h2>
            <p style={{ fontSize: '13px', color: '#666360', marginBottom: '20px', lineHeight: '1.6' }}>
              The application encountered an unexpected error. Click below to reload.
            </p>
            <button
              onClick={() => window.location.reload()}
              style={{
                background: '#D97757',
                color: '#FFFFFF',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '8px',
                fontWeight: '600',
                fontSize: '13px',
                cursor: 'pointer'
              }}
            >
              Reload Application
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
);

