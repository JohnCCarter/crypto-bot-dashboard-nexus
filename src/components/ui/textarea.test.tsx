import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { Textarea } from './textarea';


describe('Textarea', () => {
  it('renderar en textarea', () => {
    render(<Textarea />);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('visar placeholder', () => {
    render(<Textarea placeholder="Skriv här" />);
    expect(screen.getByPlaceholderText('Skriv här')).toBeInTheDocument();
  });

  it('kan vara disabled', () => {
    render(<Textarea disabled />);
    expect(screen.getByRole('textbox')).toBeDisabled();
  });

  it('accepterar textinmatning', async () => {
    render(<Textarea />);
    const textarea = screen.getByRole('textbox');
    await userEvent.type(textarea, 'Hej världen!');
    expect(textarea).toHaveValue('Hej världen!');
  });
}); 