// Import ReactDOM's createRoot for rendering the application
// Import the main application component
import App from './App.tsx';
// Import global styles
import { createRoot } from 'react-dom/client';
import './index.css';

// React DevTools-scriptinjektion borttagen för att undvika CORS- och nätverksfel.

const rootElement = document.getElementById("root");
if (rootElement) {
  createRoot(rootElement).render(<App />);
} else {
  console.error("Root element not found. Unable to render the application.");
}
