/**
 * XPathCachePanel — Sprint 10.16
 *
 * Settings panel for managing the XPath cache used by Tier-2 execution.
 *
 * Features:
 *  - Stats row: total, valid, invalid entries + total hits
 *  - Keyword filter: search by instruction or page_url substring
 *  - Entries table: instruction (truncated), page_url (truncated), hits, valid badge, delete button
 *  - "Clear Invalid" — removes only is_valid=false entries, keeps correct XPaths
 *  - "Clear All"     — removes every entry (replaces the previous Python one-liner)
 */
import React, { useCallback, useEffect, useRef, useState } from 'react';
import settingsService from '../services/settingsService';

// ---------------------------------------------------------------------------
// Types (local; mirrors backend XPathCache schema)
// ---------------------------------------------------------------------------

interface XPathCacheEntry {
  id: number;
  instruction: string;
  page_url: string;
  xpath: string;
  cache_key: string;
  selector_type: string;
  is_valid: boolean;
  hit_count: number;
  validation_failures: number;
  extraction_time_ms: number | null;
  page_title: string | null;
  element_text: string | null;
  created_at: string;
  updated_at: string | null;
}

interface XPathCacheStats {
  total_entries: number;
  valid_entries: number;
  invalid_entries: number;
  total_hits: number;
  avg_extraction_time_ms: number;
  cache_hit_rate: number;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function truncate(s: string, max = 60): string {
  return s.length <= max ? s : `${s.slice(0, max)}…`;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export const XPathCachePanel: React.FC = () => {
  const [stats, setStats] = useState<XPathCacheStats | null>(null);
  const [entries, setEntries] = useState<XPathCacheEntry[]>([]);
  const [keyword, setKeyword] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ---- data fetching -------------------------------------------------------

  const loadData = useCallback(async (kw?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const [statsRes, listRes] = await Promise.all([
        settingsService.getXPathCacheStats(),
        settingsService.getXPathCacheEntries(kw || undefined),
      ]);
      setStats(statsRes);
      setEntries(listRes.entries);
    } catch {
      setError('Failed to load XPath cache data. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // ---- keyword filter with 400 ms debounce --------------------------------

  const handleKeywordChange = (value: string) => {
    setKeyword(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      settingsService.getXPathCacheEntries(value || undefined).then((res) => {
        setEntries(res.entries);
      });
    }, 400);
  };

  // ---- per-entry delete ---------------------------------------------------

  const handleDelete = async (entry: XPathCacheEntry) => {
    if (!confirm(`Delete XPath cache for:\n"${entry.instruction}"\n\nThis step will re-learn its XPath on the next run.`)) {
      return;
    }
    try {
      await settingsService.deleteXPathCacheEntry(entry.id);
      showMessage('success', `Deleted cache for: ${truncate(entry.instruction, 50)}`);
      await loadData(keyword || undefined);
    } catch {
      showMessage('error', 'Failed to delete cache entry.');
    }
  };

  // ---- bulk clear ---------------------------------------------------------

  const handleClearInvalid = async () => {
    if (!confirm('Remove all invalid (failed) XPath cache entries?\n\nValid entries will be kept.')) return;
    try {
      const res = await settingsService.clearXPathCache(true);
      showMessage('success', res.message);
      await loadData(keyword || undefined);
    } catch {
      showMessage('error', 'Failed to clear invalid entries.');
    }
  };

  const handleClearAll = async () => {
    if (!confirm('Clear ALL XPath cache entries?\n\nEvery step will re-learn its XPath on the next run.')) return;
    try {
      const res = await settingsService.clearXPathCache(false);
      showMessage('success', res.message);
      await loadData(keyword || undefined);
    } catch {
      showMessage('error', 'Failed to clear all cache entries.');
    }
  };

  const showMessage = (type: 'success' | 'error', text: string) => {
    setActionMessage({ type, text });
    setTimeout(() => setActionMessage(null), 4000);
  };

  // ---- render --------------------------------------------------------------

  return (
    <div className="space-y-4">
      {/* Header + action buttons */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h3 className="text-base font-semibold text-gray-900">XPath Cache</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Tier-2 execution caches element XPaths to avoid repeated LLM observe() calls.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleClearInvalid}
            className="px-3 py-1.5 text-xs font-medium rounded-md bg-amber-50 text-amber-700 border border-amber-200 hover:bg-amber-100 transition-colors"
          >
            Clear Invalid
          </button>
          <button
            onClick={handleClearAll}
            className="px-3 py-1.5 text-xs font-medium rounded-md bg-red-50 text-red-700 border border-red-200 hover:bg-red-100 transition-colors"
          >
            Clear All
          </button>
        </div>
      </div>

      {/* Action feedback */}
      {actionMessage && (
        <div
          className={`p-3 rounded-lg text-sm ${
            actionMessage.type === 'success'
              ? 'bg-green-50 border border-green-200 text-green-800'
              : 'bg-red-50 border border-red-200 text-red-800'
          }`}
        >
          {actionMessage.text}
        </div>
      )}

      {/* Loading / error guards */}
      {isLoading && (
        <div className="flex items-center gap-2 text-sm text-gray-500 py-4">
          <span className="animate-spin inline-block">⏳</span> Loading...
        </div>
      )}
      {!isLoading && error && (
        <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-800">{error}</div>
      )}

      {/* Stats row */}
      {!isLoading && !error && stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Total', value: stats.total_entries, color: 'text-gray-900' },
            { label: 'Valid', value: stats.valid_entries, color: 'text-green-700' },
            { label: 'Invalid', value: stats.invalid_entries, color: 'text-red-600' },
            { label: 'Hits', value: stats.total_hits, color: 'text-blue-700' },
          ].map(({ label, value, color }) => (
            <div key={label} className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-center">
              <p className={`text-xl font-bold ${color}`}>{value}</p>
              <p className="text-xs text-gray-500 mt-0.5">{label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Keyword filter */}
      {!isLoading && !error && (
        <input
          type="text"
          value={keyword}
          onChange={(e) => handleKeywordChange(e.target.value)}
          placeholder="Filter by instruction or URL…"
          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
        />
      )}

      {/* Entries table */}
      {!isLoading && !error && entries.length === 0 && (
        <p className="text-sm text-gray-500 py-3 text-center">
          No XPath cache entries{keyword ? ` matching "${keyword}"` : ''}.
        </p>
      )}

      {!isLoading && !error && entries.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="w-full text-xs">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-3 py-2 text-left text-gray-600 font-medium">Instruction</th>
                <th className="px-3 py-2 text-left text-gray-600 font-medium hidden sm:table-cell">Page URL</th>
                <th className="px-3 py-2 text-center text-gray-600 font-medium">Hits</th>
                <th className="px-3 py-2 text-center text-gray-600 font-medium">Status</th>
                <th className="px-3 py-2 text-center text-gray-600 font-medium">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {entries.map((entry) => (
                <tr key={entry.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-3 py-2 text-gray-800 max-w-xs" title={entry.instruction}>
                    {truncate(entry.instruction)}
                  </td>
                  <td className="px-3 py-2 text-gray-500 max-w-xs hidden sm:table-cell" title={entry.page_url}>
                    {truncate(entry.page_url, 45)}
                  </td>
                  <td className="px-3 py-2 text-center text-gray-700 font-mono">{entry.hit_count}</td>
                  <td className="px-3 py-2 text-center">
                    {entry.is_valid ? (
                      <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                        Valid
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
                        Invalid
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-center">
                    <button
                      onClick={() => handleDelete(entry)}
                      title="Delete this cache entry"
                      className="p-1.5 rounded text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                      aria-label="Delete"
                    >
                      🗑
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!isLoading && !error && stats && (
        <p className="text-xs text-gray-400">
          Avg extraction: {stats.avg_extraction_time_ms.toFixed(0)} ms · Cache hit rate: {stats.cache_hit_rate.toFixed(2)}x
        </p>
      )}
    </div>
  );
};
