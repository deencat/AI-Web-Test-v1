import React, { useState, useEffect } from 'react';
import { X, GitCompare, Calendar, User } from 'lucide-react';

interface Version {
  id: number;
  version_number: number;
  steps: string[];
  created_at: string;
  created_by: string;
}

interface ComparisonResult {
  version_1: Version;
  version_2: Version;
  steps_changed: boolean;
  steps_count_diff: number | null;
}

interface VersionCompareDialogProps {
  testId: number;
  versionId1: number;
  versionId2: number;
  isOpen: boolean;
  onClose: () => void;
}

export const VersionCompareDialog: React.FC<VersionCompareDialogProps> = ({
  testId,
  versionId1,
  versionId2,
  isOpen,
  onClose
}) => {
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && versionId1 && versionId2) {
      loadComparison();
    }
  }, [isOpen, versionId1, versionId2, testId]);

  const loadComparison = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(
        `http://localhost:8000/api/v1/tests/${testId}/versions/compare/${versionId1}/${versionId2}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to compare versions');
      }

      const data = await response.json();
      setComparison(data);
      console.log('✅ Loaded comparison:', data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load comparison');
      console.error('Load comparison error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Simple diff algorithm for highlighting changes
  const getStepDiff = (steps1: string[], steps2: string[]) => {
    const maxLength = Math.max(steps1.length, steps2.length);
    const diff: Array<{ left: string | null; right: string | null; type: 'same' | 'added' | 'removed' | 'modified' }> = [];

    for (let i = 0; i < maxLength; i++) {
      const step1 = steps1[i];
      const step2 = steps2[i];

      if (step1 === undefined) {
        diff.push({ left: null, right: step2, type: 'added' });
      } else if (step2 === undefined) {
        diff.push({ left: step1, right: null, type: 'removed' });
      } else if (step1 === step2) {
        diff.push({ left: step1, right: step2, type: 'same' });
      } else {
        diff.push({ left: step1, right: step2, type: 'modified' });
      }
    }

    return diff;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Dialog */}
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] flex flex-col z-50 m-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <GitCompare className="w-6 h-6 text-blue-600" />
            <h2 className="text-2xl font-bold text-gray-900">Compare Versions</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-3 text-gray-600">Loading comparison...</span>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {comparison && !loading && (
            <div className="space-y-6">
              {/* Version Info Header */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-semibold text-blue-900">Version {comparison.version_1.version_number}</span>
                    <span className="text-xs text-blue-600">(Older)</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Calendar className="w-4 h-4" />
                    <span>{formatDate(comparison.version_1.created_at)}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-600 mt-1">
                    <User className="w-4 h-4" />
                    <span>{comparison.version_1.created_by}</span>
                  </div>
                </div>

                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-semibold text-green-900">Version {comparison.version_2.version_number}</span>
                    <span className="text-xs text-green-600">(Newer)</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Calendar className="w-4 h-4" />
                    <span>{formatDate(comparison.version_2.created_at)}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-600 mt-1">
                    <User className="w-4 h-4" />
                    <span>{comparison.version_2.created_by}</span>
                  </div>
                </div>
              </div>

              {/* Summary */}
              {comparison.steps_changed && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <p className="text-sm text-yellow-800">
                    <strong>Changes detected:</strong> Steps have been modified
                    {comparison.steps_count_diff !== null && comparison.steps_count_diff !== 0 && (
                      <span className="ml-2">
                        ({comparison.steps_count_diff > 0 ? '+' : ''}{comparison.steps_count_diff} step{comparison.steps_count_diff !== 1 ? 's' : ''})
                      </span>
                    )}
                  </p>
                </div>
              )}

              {/* Side-by-side Comparison */}
              <div className="grid grid-cols-2 gap-4">
                {/* Left: Version 1 */}
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <div className="bg-blue-100 px-4 py-2 border-b border-gray-200">
                    <h3 className="font-semibold text-blue-900">Version {comparison.version_1.version_number}</h3>
                  </div>
                  <div className="p-4 bg-gray-50 max-h-96 overflow-y-auto">
                    {comparison.version_1.steps.length === 0 ? (
                      <p className="text-gray-400 italic">No steps</p>
                    ) : (
                      <ol className="space-y-2 list-decimal list-inside">
                        {comparison.version_1.steps.map((step, index) => (
                          <li key={index} className="text-sm text-gray-700 mb-3">
                            <span className="font-mono bg-white px-2 py-1 rounded border border-gray-200 block">
                              {step}
                            </span>
                          </li>
                        ))}
                      </ol>
                    )}
                  </div>
                </div>

                {/* Right: Version 2 */}
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <div className="bg-green-100 px-4 py-2 border-b border-gray-200">
                    <h3 className="font-semibold text-green-900">Version {comparison.version_2.version_number}</h3>
                  </div>
                  <div className="p-4 bg-gray-50 max-h-96 overflow-y-auto">
                    {comparison.version_2.steps.length === 0 ? (
                      <p className="text-gray-400 italic">No steps</p>
                    ) : (
                      <ol className="space-y-2 list-decimal list-inside">
                        {getStepDiff(comparison.version_1.steps, comparison.version_2.steps).map((diff, index) => (
                          <li key={index} className="text-sm mb-3">
                            {diff.right !== null ? (
                              <span
                                className={`font-mono px-2 py-1 rounded border block ${
                                  diff.type === 'added'
                                    ? 'bg-green-100 border-green-300 text-green-800'
                                    : diff.type === 'modified'
                                    ? 'bg-yellow-100 border-yellow-300 text-yellow-800'
                                    : 'bg-white border-gray-200 text-gray-700'
                                }`}
                              >
                                {diff.right}
                              </span>
                            ) : (
                              <span className="text-gray-400 italic">(removed)</span>
                            )}
                          </li>
                        ))}
                      </ol>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

