// Import ReactDOM's createRoot for rendering the application
// Import the main application component
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from '@/components/ui/toaster';
import { WebSocketMarketProvider } from '@/contexts/WebSocketMarketProvider';
import Index from '@/pages/Index';
import { HybridDemo } from '@/pages/HybridDemo';
import NotFound from '@/pages/NotFound';
// Import global styles
import './index.css';

// Create a React Query client with trading-optimized settings
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes cache
      refetchOnWindowFocus: false, // Avoid unnecessary requests
      refetchOnReconnect: true, // Update on reconnect
      retry: 1, // ⭐ CRITICAL: Reduced from 3 to 1 for faster error feedback
      retryDelay: 1000, // 1 second between retries (faster than exponential backoff)
    },
  },
});

const rootElement = document.getElementById("root");
if (rootElement) {
  const root = createRoot(rootElement);

  root.render(
    <StrictMode>
      <QueryClientProvider client={queryClient}>
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
      </QueryClientProvider>
    </StrictMode>
  );
} else {
  console.error("Root element not found. Unable to render the application.");
}
