import { OrderHistory } from '@/components/OrderHistory';
import { api } from '@/lib/api';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';

vi.mock('@/lib/api');

// Skapa en mockad toast-funktion
const toastMock = vi.fn();
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: toastMock })
}));

const mockedApi = api as unknown as ReturnType<typeof vi.mocked<typeof api>>;

describe('OrderHistory', () => {
  const orders = [
    {
      id: 'order1',
      symbol: 'BTC/USD',
      order_type: 'limit' as const,
      side: 'buy' as const,
      amount: 0.1,
      price: 27000,
      fee: 1.5,
      status: 'pending' as const,
      timestamp: new Date().toISOString(),
    },
    {
      id: 'order2',
      symbol: 'ETH/USD',
      order_type: 'market' as const,
      side: 'sell' as const,
      amount: 0.2,
      price: 1800,
      fee: 0.8,
      status: 'filled' as const,
      timestamp: new Date().toISOString(),
    },
  ];

  beforeEach(() => {
    toastMock.mockClear();
  });

  it('avbryter en pending order och visar feedback', async () => {
    mockedApi.cancelOrder.mockResolvedValueOnce({ message: 'Order cancelled' });
    const onOrderCancelled = vi.fn();
    render(<OrderHistory orders={orders} onOrderCancelled={onOrderCancelled} />);

    fireEvent.click(screen.getByText('Avbryt'));

    await waitFor(() => {
      expect(mockedApi.cancelOrder).toHaveBeenCalledWith('order1');
      expect(toastMock).toHaveBeenCalledWith(
        expect.objectContaining({ title: 'Order Cancelled' })
      );
      expect(onOrderCancelled).toHaveBeenCalled();
    });
  });

  it('visar felmeddelande vid misslyckad avbrytning', async () => {
    mockedApi.cancelOrder.mockRejectedValueOnce(new Error('fail'));
    render(<OrderHistory orders={orders} />);
    fireEvent.click(screen.getByText('Avbryt'));
    await waitFor(() => {
      expect(toastMock).toHaveBeenCalledWith(
        expect.objectContaining({ title: 'Cancellation Failed' })
      );
    });
  });
}); 