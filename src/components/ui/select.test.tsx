import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { Select, SelectContent, SelectItem, SelectTrigger } from './select';

// Mocka Radix UI Select för testmiljön (jsdom saknar hasPointerCapture)
vi.mock('@radix-ui/react-select', () => {
  return {
    __esModule: true,
    Root: ({ children }: { children: React.ReactNode }) => <div data-testid="mock-select">{children}</div>,
    Group: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    Value: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
    Trigger: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => <button {...props}>{children}</button>,
    Content: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    Item: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => <div {...props}>{children}</div>,
    ItemText: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
    Label: ({ children }: { children: React.ReactNode }) => <label>{children}</label>,
    Separator: () => <hr />,
    ScrollUpButton: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    ScrollDownButton: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    Icon: ({ children }: { children: React.ReactNode }) => <span data-testid="mock-icon">{children}</span>,
    Portal: ({ children }: { children: React.ReactNode }) => <div data-testid="mock-portal">{children}</div>,
    Viewport: ({ children }: { children: React.ReactNode }) => <div data-testid="mock-viewport">{children}</div>,
    ItemIndicator: ({ children }: { children: React.ReactNode }) => <span data-testid="mock-item-indicator">{children}</span>,
  };
});

describe('Select', () => {
  it('renderar en select-trigger', () => {
    render(
      <Select>
        <SelectTrigger>Välj frukt</SelectTrigger>
        <SelectContent>
          <SelectItem value="apple">Äpple</SelectItem>
          <SelectItem value="banana">Banan</SelectItem>
        </SelectContent>
      </Select>
    );
    expect(screen.getByRole('button')).toBeInTheDocument();
    expect(screen.getByText('Välj frukt')).toBeInTheDocument();
  });

  // Skippad: avancerad menyinteraktion kan ej testas med mockad Radix UI Select i jsdom
  it.skip('kan öppna meny och välja alternativ', () => {
    // Detta test är skippat p.g.a. mockad Select-komponent (jsdom saknar stöd för Radix UI interaktion)
  });

  it('kan vara disabled', () => {
    render(
      <Select>
        <SelectTrigger disabled>Välj frukt</SelectTrigger>
      </Select>
    );
    expect(screen.getByRole('button')).toBeDisabled();
  });
}); 