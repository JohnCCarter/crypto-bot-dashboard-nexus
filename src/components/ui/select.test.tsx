import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { Select, SelectTrigger, SelectContent, SelectItem, SelectValue } from './select';


describe('Select', () => {
  it('renderar en select-trigger', () => {
    render(
      <Select>
        <SelectTrigger aria-label="Välj frukt" />
        <SelectContent>
          <SelectItem value="apple">Äpple</SelectItem>
          <SelectItem value="banana">Banan</SelectItem>
        </SelectContent>
      </Select>
    );
    expect(screen.getByRole('combobox', { name: /välj frukt/i })).toBeInTheDocument();
  });

  it('kan öppna meny och välja alternativ', async () => {
    render(
      <Select>
        <SelectTrigger aria-label="Välj frukt" />
        <SelectContent>
          <SelectItem value="apple">Äpple</SelectItem>
          <SelectItem value="banana">Banan</SelectItem>
        </SelectContent>
      </Select>
    );
    const trigger = screen.getByRole('combobox', { name: /välj frukt/i });
    await userEvent.click(trigger);
    expect(screen.getByText('Äpple')).toBeInTheDocument();
    await userEvent.click(screen.getByText('Banan'));
    // Efter val ska menyn stängas och triggern visa det valda värdet
    expect(trigger).toHaveTextContent(/banan/i);
  });

  it('kan vara disabled', () => {
    render(
      <Select disabled>
        <SelectTrigger aria-label="Välj frukt" />
        <SelectContent>
          <SelectItem value="apple">Äpple</SelectItem>
        </SelectContent>
      </Select>
    );
    expect(screen.getByRole('combobox', { name: /välj frukt/i })).toBeDisabled();
  });
}); 