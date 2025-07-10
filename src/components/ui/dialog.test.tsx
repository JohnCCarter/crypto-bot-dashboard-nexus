import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { Dialog, DialogContent, DialogDescription, DialogTitle, DialogTrigger } from './dialog';


describe('Dialog', () => {
  it('renderar och öppnar dialogen', async () => {
    render(
      <Dialog>
        <DialogTrigger>Öppna dialog</DialogTrigger>
        <DialogContent>
          <DialogTitle>Testdialog</DialogTitle>
          <DialogDescription>Detta är en testdialog.</DialogDescription>
        </DialogContent>
      </Dialog>
    );
    // Dialogen ska inte synas initialt
    expect(screen.queryByText('Testdialog')).not.toBeInTheDocument();
    // Klicka på triggern
    await userEvent.click(screen.getByText('Öppna dialog'));
    // Nu ska dialogen synas
    expect(screen.getByText('Testdialog')).toBeInTheDocument();
    expect(screen.getByText('Detta är en testdialog.')).toBeInTheDocument();
    // Stäng dialogen via close-knappen (X)
    const closeButton = screen.getByRole('button', { name: /close/i });
    await userEvent.click(closeButton);
    expect(screen.queryByText('Testdialog')).not.toBeInTheDocument();
  });
}); 