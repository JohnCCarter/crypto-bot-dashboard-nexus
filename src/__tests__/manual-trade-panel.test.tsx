import { ManualTradePanel } from '@/components/ManualTradePanel';
import { api } from '@/lib/api';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';

vi.mock('@/lib/api');

// Skapa en mockad toast-funktion
const toastMock = vi.fn();
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: toastMock })
}));

// Mock WebSocketMarketProvider
vi.mock('@/contexts/WebSocketMarketProvider', () => ({
  useGlobalWebSocketMarket: () => ({
    tickers: {
      'TESTBTC/TESTUSD': {
        symbol: 'TESTBTC/TESTUSD',
        price: 50000,
        volume: 1000,
        bid: 49995,
        ask: 50005,
        timestamp: new Date().toISOString()
      }
    },
    orderbooks: {},
    trades: {},
    connected: true,
    connecting: false,
    platformStatus: 'operative',
    error: null,
    lastHeartbeat: Date.now(),
    latency: 50,
    subscribeToSymbol: vi.fn(),
    unsubscribeFromSymbol: vi.fn(),
    getTickerForSymbol: vi.fn(() => ({
      symbol: 'TESTBTC/TESTUSD',
      price: 50000,
      volume: 1000,
      bid: 49995,
      ask: 50005,
      timestamp: new Date().toISOString()
    })),
    getOrderbookForSymbol: vi.fn(() => null),
    getTradesForSymbol: vi.fn(() => []),
    userFills: [],
    liveOrders: {},
    liveBalances: {},
    userDataConnected: true,
    userDataError: null,
    subscribeToUserData: vi.fn().mockResolvedValue(undefined),
    unsubscribeFromUserData: vi.fn().mockResolvedValue(undefined),
  }),
  WebSocketMarketProvider: ({ children }: { children: React.ReactNode }) => children
}));

const mockedApi = api as jest.Mocked<typeof api>;

// Helper för att wrappa komponenter med QueryClient
const renderWithQueryClient = (ui: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  });
  
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
};

describe('ManualTradePanel', () => {
  beforeEach(() => {
    toastMock.mockClear();
    mockedApi.placeOrder.mockClear();
    // Mock balances API call
    mockedApi.getBalances.mockResolvedValue([
      { currency: 'TESTUSD', available: 10000, total: 10000 },
      { currency: 'TESTBTC', available: 1, total: 1 }
    ]);
  });

  it('lägger en market order och visar feedback', async () => {
    mockedApi.placeOrder.mockResolvedValueOnce({ order: { id: '12345', status: 'pending' } });
    const onOrderPlaced = vi.fn();
    renderWithQueryClient(<ManualTradePanel onOrderPlaced={onOrderPlaced} />);

    // Vänta på att komponenten renderas med trading pair
    await waitFor(() => {
      expect(screen.getByText('Manual Trading (TESTBTC/TESTUSD)')).toBeInTheDocument();
    });

    // Fyll i amount
    const amountInput = screen.getByLabelText(/amount/i);
    fireEvent.change(amountInput, { target: { value: '0.1' } });
    
    // Hitta submit-knappen genom att leta efter en button som innehåller "Buy"
    await waitFor(() => {
      const submitButton = screen.getByRole('button', { name: /buy/i });
      expect(submitButton).toBeInTheDocument();
      fireEvent.click(submitButton);
    });

    // Vänta på att order-anropet görs
    await waitFor(() => {
      expect(mockedApi.placeOrder).toHaveBeenCalledWith({
        symbol: 'TESTBTC/TESTUSD',
        order_type: 'market',
        side: 'buy',
        amount: 0.1,
        position_type: 'spot'
      });
    });

    // Vänta på toast och callback feedback
    await waitFor(() => {
      expect(toastMock).toHaveBeenCalledWith(
        expect.objectContaining({ title: 'Order Submitted' })
      );
      expect(onOrderPlaced).toHaveBeenCalled();
    });
  });

  it('visar felmeddelande vid ogiltig amount', async () => {
    renderWithQueryClient(<ManualTradePanel />);
    
    // Vänta på att komponenten renderas
    await waitFor(() => {
      expect(screen.getByText('Manual Trading (TESTBTC/TESTUSD)')).toBeInTheDocument();
    });

    // Sätt amount till 0 (ogiltigt)
    const amountInput = screen.getByLabelText(/amount/i);
    fireEvent.change(amountInput, { target: { value: '0' } });
    
    // Kontrollera att submit-knappen blir disabled
    await waitFor(() => {
      const submitButton = screen.getByRole('button', { name: /buy/i });
      expect(submitButton).toBeDisabled();
    });

    // Ingen API-call ska ske eftersom knappen är disabled
    expect(mockedApi.placeOrder).not.toHaveBeenCalled();
  });
}); 