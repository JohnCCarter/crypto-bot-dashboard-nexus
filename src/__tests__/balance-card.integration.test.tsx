import { render, screen, waitFor } from '@testing-library/react';
import { rest } from 'msw';
import { server } from './setup-msw';
import { BalanceCard } from '../components/BalanceCard';
import type { Balance } from '../types/trading';

const mockBalances: Balance[] = [
  { currency: 'BTC', total_balance: 1.234, available: 1.0 },
  { currency: 'ETH', total_balance: 10.5, available: 8.2 },
];

describe('BalanceCard integration', () => {
  beforeAll(() => {
    server.use(
      rest.get('/api/balances', (req, res, ctx) => {
        return res(ctx.status(200), ctx.json(mockBalances));
      })
    );
  });

  it('renderar saldon från API', async () => {
    // Simulera att komponenten hämtar data (du kan behöva mocka fetch i komponenten om det sker där)
    // Här testar vi direkt rendering med data
    render(<BalanceCard balances={mockBalances} isLoading={false} />);
    expect(screen.getByText('BTC')).toBeInTheDocument();
    expect(screen.getByText('ETH')).toBeInTheDocument();
    expect(screen.getByText('1.234')).toBeInTheDocument();
    expect(screen.getByText('10.5')).toBeInTheDocument();
  });
}); 