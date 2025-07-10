import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { Button } from './button';


describe('Button', () => {
  it('renderar med text', () => {
    render(<Button>Testknapp</Button>);
    expect(screen.getByRole('button', { name: /testknapp/i })).toBeInTheDocument();
  });

  it('kan vara disabled', () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
}); 