// Import ReactDOM's createRoot for rendering the application
// Import the main application component
import App from './App.tsx';
// Import global styles
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';

// Initialize production logging suppression
import './utils/logger';

// React DevTools-scriptinjektion borttagen för att undvika CORS- och nätverksfel.

const rootElement = document.getElementById("root");
if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>
  );
} else {
  console.error("Root element not found. Unable to render the application.");
}
