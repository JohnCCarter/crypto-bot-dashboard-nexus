import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { Input } from './input';


describe('Input', () => {
  it('renderar ett inputfält', () => {
    render(<Input />);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('visar placeholder', () => {
    render(<Input placeholder="Skriv här" />);
    expect(screen.getByPlaceholderText('Skriv här')).toBeInTheDocument();
  });

  it('kan vara disabled', () => {
    render(<Input disabled />);
    expect(screen.getByRole('textbox')).toBeDisabled();
  });
}); 