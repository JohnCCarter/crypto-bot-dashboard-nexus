import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './tabs';


describe('Tabs', () => {
  it('renderar tabs och visar rätt innehåll', async () => {
    render(
      <Tabs defaultValue="tab1">
        <TabsList>
          <TabsTrigger value="tab1">Tabb 1</TabsTrigger>
          <TabsTrigger value="tab2">Tabb 2</TabsTrigger>
        </TabsList>
        <TabsContent value="tab1">Innehåll 1</TabsContent>
        <TabsContent value="tab2">Innehåll 2</TabsContent>
      </Tabs>
    );
    expect(screen.getByText('Tabb 1')).toBeInTheDocument();
    expect(screen.getByText('Tabb 2')).toBeInTheDocument();
    expect(screen.getByText('Innehåll 1')).toBeVisible();
    expect(screen.queryByText('Innehåll 2')).toBeNull();
    await userEvent.click(screen.getByText('Tabb 2'));
    expect(screen.getByText('Innehåll 2')).toBeVisible();
    expect(screen.queryByText('Innehåll 1')).toBeNull();
  });

  it('kan ha en disabled-tab som inte kan aktiveras', async () => {
    render(
      <Tabs defaultValue="tab1">
        <TabsList>
          <TabsTrigger value="tab1">Tabb 1</TabsTrigger>
          <TabsTrigger value="tab2" disabled>Tabb 2</TabsTrigger>
        </TabsList>
        <TabsContent value="tab1">Innehåll 1</TabsContent>
        <TabsContent value="tab2">Innehåll 2</TabsContent>
      </Tabs>
    );
    const disabledTab = screen.getByText('Tabb 2');
    expect(disabledTab).toBeDisabled();
    await userEvent.click(disabledTab);
    // Innehåll 2 ska inte visas eftersom tabben är disabled
    expect(screen.queryByText('Innehåll 2')).toBeNull();
    expect(screen.getByText('Innehåll 1')).toBeVisible();
  });
}); 