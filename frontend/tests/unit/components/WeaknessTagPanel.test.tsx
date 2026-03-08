import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import WeaknessTagPanel from '../../../src/pages/students/WeaknessTagPanel';

// Mock API
vi.mock('../../../src/api/weakness', () => ({
  weaknessApi: {
    getStudentWeaknesses: vi.fn(() => Promise.resolve([
      { id: 1, module_name: '数量关系', level: 'red', accuracy_rate: 45 },
      { id: 2, module_name: '言语理解', level: 'yellow', accuracy_rate: 65 },
    ])),
    getModules: vi.fn(() => Promise.resolve([
      { id: 1, level1: '数量关系', level2: '数学运算' },
      { id: 2, level1: '言语理解', level2: '逻辑填空' },
    ])),
    createWeakness: vi.fn(() => Promise.resolve({ id: 3 })),
    deleteWeakness: vi.fn(() => Promise.resolve()),
    updateWeakness: vi.fn(() => Promise.resolve()),
  },
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('WeaknessTagPanel', () => {
  it('renders weakness tags', async () => {
    render(<WeaknessTagPanel studentId={1} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/数量关系/)).toBeInTheDocument();
      expect(screen.getByText(/言语理解/)).toBeInTheDocument();
    });
  });

  it('opens modal when add button clicked', async () => {
    render(<WeaknessTagPanel studentId={1} />, { wrapper });

    const addButton = await screen.findByRole('button', { name: /添加/ });
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(screen.getByText('添加薄弱项')).toBeInTheDocument();
    });
  });
});
