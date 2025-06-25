// Import ReactDOM's createRoot for rendering the application
// Import the main application component
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from '@/components/ui/toaster';
import { WebSocketMarketProvider } from '@/contexts/WebSocketMarketProvider';
import Index from '@/pages/Index';
import { HybridDemo } from '@/pages/HybridDemo';
import NotFound from '@/pages/NotFound';
// Import global styles
import './index.css';

const rootElement = document.getElementById("root");
if (rootElement) {
  const root = createRoot(rootElement);

  root.render(
    <StrictMode>
      <WebSocketMarketProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/hybrid" element={<HybridDemo />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
          <Toaster />
        </BrowserRouter>
      </WebSocketMarketProvider>
    </StrictMode>
  );
} else {
  console.error("Root element not found. Unable to render the application.");
}
