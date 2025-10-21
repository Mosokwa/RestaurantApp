import React from 'react';
import { useSelector } from 'react-redux';

class CSRFErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    // Check if error is CSRF related
    if (error.message.includes('CSRF') || error.status === 403) {
      return { hasError: true, error: 'CSRF token validation failed' };
    }
    return { hasError: true, error: error.message };
  }

  componentDidCatch(error, errorInfo) {
    console.error('CSRF Error Boundary caught an error:', error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render() {
    const { csrfError } = this.props;
    
    if (this.state.hasError || csrfError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-red-50 p-4">
          <div className="max-w-md w-full bg-white p-6 rounded-lg shadow-md">
            <div className="text-red-600 text-center">
              <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <h2 className="text-lg font-bold mb-2">Security Token Error</h2>
              <p className="text-sm text-gray-600 mb-4">
                {this.state.error || csrfError || 'There was an issue with security tokens.'}
              </p>
              <div className="space-y-2">
                <button
                  onClick={this.handleRetry}
                  className="w-full bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 text-sm"
                >
                  Refresh Page & Retry
                </button>
                <button
                  onClick={() => {
                    localStorage.clear();
                    window.location.href = '/owner/login';
                  }}
                  className="w-full bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 text-sm"
                >
                  Clear Data & Login Again
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Connected component to access Redux state
const ConnectedCSRFErrorBoundary = (props) => {
  const csrfError = useSelector(state => state.auth.csrfError);
  
  return (
    <CSRFErrorBoundary {...props} csrfError={csrfError} />
  );
};

export default ConnectedCSRFErrorBoundary;