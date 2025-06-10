import { ManualTradePanel } from '@/components/ManualTradePanel';
import { api } from '@/lib/api';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';

vi.mock('@/lib/api');

// Skapa en mockad toast-funktion
const toastMock = vi.fn();
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: toastMock })
}));
const mockedApi = api as jest.Mocked<typeof api>;

describe('ManualTradePanel', () => {
  beforeEach(() => {
    toastMock.mockClear();
  });

  it('lägger en market order och visar feedback', async () => {
    mockedApi.placeOrder.mockResolvedValueOnce({ message: 'Order placed' });
    const onOrderPlaced = vi.fn();
    render(<ManualTradePanel onOrderPlaced={onOrderPlaced} />);

    // Fyll i amount
    fireEvent.change(screen.getByLabelText(/amount/i), { target: { value: '0.1' } });
    // Klicka på Buy
    fireEvent.click(screen.getByText('Buy'));

    // Vänta på feedback
    await waitFor(() => {
      expect(mockedApi.placeOrder).toHaveBeenCalled();
      expect(toastMock).toHaveBeenCalledWith(
        expect.objectContaining({ title: 'Order Submitted' })
      );
      expect(onOrderPlaced).toHaveBeenCalled();
    });
  });

  it('visar felmeddelande vid ogiltig amount', async () => {
    render(<ManualTradePanel />);
    fireEvent.change(screen.getByLabelText(/amount/i), { target: { value: '0' } });
    fireEvent.click(screen.getByText('Buy'));
    await waitFor(() => {
      expect(toastMock).toHaveBeenCalledWith(
        expect.objectContaining({ title: 'Invalid Amount' })
      );
    });
  });
}); 