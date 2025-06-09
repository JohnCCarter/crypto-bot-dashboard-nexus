import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { Toggle } from './toggle';


describe('Toggle', () => {
  it('renderar en toggle-knapp', () => {
    render(<Toggle aria-label="Växla" />);
    expect(screen.getByRole('button', { name: /växla/i })).toBeInTheDocument();
  });

  it('kan togglas på och av', async () => {
    render(<Toggle aria-label="Växla" />);
    const button = screen.getByRole('button', { name: /växla/i });
    expect(button).toHaveAttribute('data-state', 'off');
    await userEvent.click(button);
    expect(button).toHaveAttribute('data-state', 'on');
    await userEvent.click(button);
    expect(button).toHaveAttribute('data-state', 'off');
  });

  it('kan vara disabled', () => {
    render(<Toggle aria-label="Växla" disabled />);
    const button = screen.getByRole('button', { name: /växla/i });
    expect(button).toBeDisabled();
  });
}); 