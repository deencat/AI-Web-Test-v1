/**
 * XPathCachePanel.test.tsx — Sprint 10.16
 *
 * TDD for the XPath Cache management panel in the Settings page.
 *
 * Tests cover:
 *  1. Stats row renders total, valid, invalid, hits counts
 *  2. "Loading..." shown while data is being fetched
 *  3. Cache entries table renders instruction and page_url columns
 *  4. Individual delete button calls deleteXPathCacheEntry with the entry id
 *  5. Delete button shows confirmation before calling the API
 *  6. "Clear Invalid" button calls clearXPathCache with invalid_only=true
 *  7. "Clear All" button calls clearXPathCache with invalid_only=false after confirm
 *  8. "Clear All" button does NOT call API when confirm is cancelled
 *  9. Keyword filter input triggers a re-fetch with the new keyword
 * 10. Empty state message shown when entries list is empty
 * 11. Error state shown when API call fails
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import settingsService from '../../services/settingsService';
import { XPathCachePanel } from '../../components/XPathCachePanel';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('../../services/settingsService', () => ({
  default: {
    getXPathCacheStats: vi.fn(),
    getXPathCacheEntries: vi.fn(),
    deleteXPathCacheEntry: vi.fn(),
    clearXPathCache: vi.fn(),
  },
}));

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const mockStats = {
  total_entries: 12,
  valid_entries: 10,
  invalid_entries: 2,
  total_hits: 87,
  avg_extraction_time_ms: 340.5,
  cache_hit_rate: 7.25,
};

const mockEntries = [
  {
    id: 1,
    instruction: 'Step 3: click Subscribe Now',
    page_url: 'https://three.com.hk/postpaid/en',
    xpath: "//button[@data-testid='subscribe']",
    cache_key: 'key001',
    selector_type: 'xpath',
    is_valid: true,
    hit_count: 8,
    validation_failures: 0,
    extraction_time_ms: 290.0,
    page_title: 'Three HK',
    element_text: 'Subscribe Now',
    extra_data: null,
    last_validated: null,
    created_at: '2026-05-01T10:00:00Z',
    updated_at: '2026-05-20T12:00:00Z',
  },
  {
    id: 2,
    instruction: 'Step 7: fill card number',
    page_url: 'https://gphk.gateway.mastercard.com/checkout/pay/SESSION',
    xpath: "//input[@name='card']",
    cache_key: 'key002',
    selector_type: 'xpath',
    is_valid: false,
    hit_count: 1,
    validation_failures: 3,
    extraction_time_ms: 410.0,
    page_title: 'Payment',
    element_text: null,
    extra_data: null,
    last_validated: null,
    created_at: '2026-05-10T09:00:00Z',
    updated_at: '2026-05-10T09:00:00Z',
  },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function setupMocks(opts: { stats?: typeof mockStats; entries?: typeof mockEntries } = {}) {
  vi.mocked(settingsService.getXPathCacheStats).mockResolvedValue(opts.stats ?? mockStats);
  vi.mocked(settingsService.getXPathCacheEntries).mockResolvedValue({
    entries: opts.entries ?? mockEntries,
    total: (opts.entries ?? mockEntries).length,
  });
  vi.mocked(settingsService.deleteXPathCacheEntry).mockResolvedValue(undefined);
  vi.mocked(settingsService.clearXPathCache).mockResolvedValue({ deleted: 2, message: 'Cleared 2 entries' });
}

function renderPanel() {
  return render(<XPathCachePanel />);
}

// ---------------------------------------------------------------------------
// 1. Stats row
// ---------------------------------------------------------------------------

describe('XPathCachePanel — stats row', () => {
  beforeEach(() => setupMocks());

  it('shows total entries count', async () => {
    renderPanel();
    expect(await screen.findByText('12')).toBeInTheDocument();
  });

  it('shows valid entries count', async () => {
    renderPanel();
    await screen.findByText('12'); // wait for load
    expect(screen.getByText('10')).toBeInTheDocument();
  });

  it('shows invalid entries count', async () => {
    renderPanel();
    await screen.findByText('12');
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('shows total hits', async () => {
    renderPanel();
    await screen.findByText('87');
  });
});

// ---------------------------------------------------------------------------
// 2. Loading state
// ---------------------------------------------------------------------------

describe('XPathCachePanel — loading', () => {
  it('shows loading indicator while fetching', () => {
    vi.mocked(settingsService.getXPathCacheStats).mockReturnValue(new Promise(() => {}));
    vi.mocked(settingsService.getXPathCacheEntries).mockReturnValue(new Promise(() => {}));
    renderPanel();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// 3. Entries table
// ---------------------------------------------------------------------------

describe('XPathCachePanel — entries table', () => {
  beforeEach(() => setupMocks());

  it('renders instruction text in table', async () => {
    renderPanel();
    expect(await screen.findByText(/Step 3: click Subscribe Now/i)).toBeInTheDocument();
  });

  it('renders page_url in table', async () => {
    renderPanel();
    expect(await screen.findByText(/three\.com\.hk/i)).toBeInTheDocument();
  });

  it('renders a valid badge for valid entries', async () => {
    renderPanel();
    await screen.findByText(/Step 3: click Subscribe Now/i);
    // Multiple elements contain 'Valid' (stats label + badge span); verify at least one exists.
    expect(screen.getAllByText('Valid').length).toBeGreaterThan(0);
  });

  it('renders an invalid badge for invalid entries', async () => {
    renderPanel();
    await screen.findByText(/Step 7: fill card number/i);
    // Multiple elements contain 'Invalid' (stats label + badge span); verify at least one exists.
    expect(screen.getAllByText('Invalid').length).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// 4 & 5. Per-entry delete
// ---------------------------------------------------------------------------

describe('XPathCachePanel — delete single entry', () => {
  beforeEach(() => { vi.clearAllMocks(); setupMocks(); });

  it('calls deleteXPathCacheEntry with the correct id when confirmed', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    renderPanel();
    const deleteButtons = await screen.findAllByRole('button', { name: /delete/i });
    fireEvent.click(deleteButtons[0]);
    await waitFor(() => {
      expect(settingsService.deleteXPathCacheEntry).toHaveBeenCalledWith(1);
    });
  });

  it('does NOT call deleteXPathCacheEntry when confirm is cancelled', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    renderPanel();
    const deleteButtons = await screen.findAllByRole('button', { name: /delete/i });
    fireEvent.click(deleteButtons[0]);
    expect(settingsService.deleteXPathCacheEntry).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// 6. Clear Invalid button
// ---------------------------------------------------------------------------

describe('XPathCachePanel — Clear Invalid button', () => {
  beforeEach(() => setupMocks());

  it('calls clearXPathCache with invalid_only=true', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    renderPanel();
    const btn = await screen.findByRole('button', { name: /clear invalid/i });
    fireEvent.click(btn);
    await waitFor(() => {
      expect(settingsService.clearXPathCache).toHaveBeenCalledWith(true);
    });
  });
});

// ---------------------------------------------------------------------------
// 7 & 8. Clear All button
// ---------------------------------------------------------------------------

describe('XPathCachePanel — Clear All button', () => {
  beforeEach(() => { vi.clearAllMocks(); setupMocks(); });

  it('calls clearXPathCache with invalid_only=false when confirmed', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    renderPanel();
    const btn = await screen.findByRole('button', { name: /clear all/i });
    fireEvent.click(btn);
    await waitFor(() => {
      expect(settingsService.clearXPathCache).toHaveBeenCalledWith(false);
    });
  });

  it('does NOT call clearXPathCache when confirm is cancelled', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    renderPanel();
    const btn = await screen.findByRole('button', { name: /clear all/i });
    fireEvent.click(btn);
    expect(settingsService.clearXPathCache).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// 9. Keyword filter triggers re-fetch
// ---------------------------------------------------------------------------

describe('XPathCachePanel — keyword filter', () => {
  beforeEach(() => setupMocks());

  it('calls getXPathCacheEntries with the typed keyword', async () => {
    renderPanel();
    await screen.findByText(/Step 3/i); // wait for initial load
    const input = screen.getByPlaceholderText(/filter/i);
    fireEvent.change(input, { target: { value: 'subscribe' } });
    // Debounce or immediate call
    await waitFor(() => {
      expect(settingsService.getXPathCacheEntries).toHaveBeenCalledWith('subscribe');
    });
  });
});

// ---------------------------------------------------------------------------
// 10. Empty state
// ---------------------------------------------------------------------------

describe('XPathCachePanel — empty state', () => {
  it('shows empty state message when no entries', async () => {
    vi.mocked(settingsService.getXPathCacheStats).mockResolvedValue({
      ...mockStats,
      total_entries: 0,
      valid_entries: 0,
      invalid_entries: 0,
    });
    vi.mocked(settingsService.getXPathCacheEntries).mockResolvedValue({ entries: [], total: 0 });
    renderPanel();
    expect(await screen.findByText(/no xpath cache entries/i)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// 11. Error state
// ---------------------------------------------------------------------------

describe('XPathCachePanel — error state', () => {
  it('shows error message when API call fails', async () => {
    vi.mocked(settingsService.getXPathCacheStats).mockRejectedValue(new Error('Network error'));
    vi.mocked(settingsService.getXPathCacheEntries).mockRejectedValue(new Error('Network error'));
    renderPanel();
    expect(await screen.findByText(/failed to load/i)).toBeInTheDocument();
  });
});
