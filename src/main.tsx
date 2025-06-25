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

// Create a React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
      retry: 1,
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
