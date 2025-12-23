import React, { useState, useEffect } from 'react';
import { X, Clock, User, RotateCcw, Eye, GitCompare } from 'lucide-react';

interface Version {
  id: number;
  version_number: number;
  test_case_id: number;
  steps: string[];
  expected_result?: string;
  test_data?: Record<string, any>;
  created_at: string;
  created_by: string;
  change_reason?: string;
  parent_version_id?: number;
}

interface VersionHistoryPanelProps {
  testId: number;
  currentVersion: number;
  isOpen: boolean;
  onClose: () => void;
  onViewVersion?: (version: Version) => void;
  onCompareVersions?: (v1: number, v2: number) => void;
  onRollback?: (versionId: number) => void;
}

export const VersionHistoryPanel: React.FC<VersionHistoryPanelProps> = ({
  testId,
  currentVersion,
  isOpen,
  onClose,
  onViewVersion,
  onCompareVersions,
  onRollback
}) => {
  const [versions, setVersions] = useState<Version[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedVersions, setSelectedVersions] = useState<number[]>([]);

  // Load versions when panel opens
  useEffect(() => {
    if (isOpen) {
      loadVersions();
    }
  }, [isOpen, testId]);

  const loadVersions = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(`http://localhost:8000/api/v1/tests/${testId}/versions`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to load versions');
      }

      const data = await response.json();
      // Backend returns array directly, not wrapped in {versions: [...]}
      setVersions(Array.isArray(data) ? data : []);
      console.log('✅ Loaded versions:', data.length, 'versions for test', testId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load versions');
      console.error('Load versions error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined 
    });
  };

  // Handle version selection for comparison
  const handleVersionSelect = (versionNumber: number) => {
    setSelectedVersions(prev => {
      if (prev.includes(versionNumber)) {
        return prev.filter(v => v !== versionNumber);
      } else if (prev.length < 2) {
        return [...prev, versionNumber];
      } else {
        // Replace oldest selection
        return [prev[1], versionNumber];
      }
    });
  };

  // Handle compare action
  const handleCompare = () => {
    if (selectedVersions.length === 2 && onCompareVersions) {
      const [v1, v2] = selectedVersions.sort((a, b) => a - b);
      onCompareVersions(v1, v2);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed right-0 top-0 h-full w-full md:w-2/3 lg:w-1/2 bg-white shadow-2xl z-50 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Version History</h2>
            <p className="text-sm text-gray-500 mt-1">
              Test Case #{testId} • Current: v{currentVersion}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Close panel"
          >
            <X className="w-6 h-6 text-gray-500" />
          </button>
        </div>

        {/* Compare button (when 2 selected) */}
        {selectedVersions.length === 2 && (
          <div className="px-6 py-3 bg-blue-50 border-b border-blue-200">
            <button
              onClick={handleCompare}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2 transition-colors"
            >
              <GitCompare className="w-4 h-4" />
              Compare v{selectedVersions[0]} and v{selectedVersions[1]}
            </button>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
              <p className="font-medium">Error loading versions</p>
              <p className="text-sm mt-1">{error}</p>
              <button
                onClick={loadVersions}
                className="mt-3 px-4 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200 text-sm"
              >
                Try Again
              </button>
            </div>
          )}

          {!loading && !error && versions.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              <Clock className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">No version history yet</p>
              <p className="text-sm mt-2">Versions will appear here when you save changes</p>
            </div>
          )}

          {!loading && !error && versions.length > 0 && (
            <div className="space-y-3">
              {versions.map((version) => (
                <div
                  key={version.id}
                  className={`border rounded-lg p-4 transition-all ${
                    version.version_number === currentVersion
                      ? 'border-blue-500 bg-blue-50'
                      : selectedVersions.includes(version.version_number)
                      ? 'border-green-500 bg-green-50'
                      : 'border-gray-200 hover:border-gray-300 bg-white'
                  }`}
                >
                  {/* Version header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={selectedVersions.includes(version.version_number)}
                        onChange={() => handleVersionSelect(version.version_number)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                        disabled={version.version_number === currentVersion}
                      />
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-lg font-bold text-gray-900">
                            Version {version.version_number}
                          </span>
                          {version.version_number === currentVersion && (
                            <span className="px-2 py-0.5 bg-blue-600 text-white text-xs font-medium rounded">
                              Current
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-4 mt-1 text-sm text-gray-600">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {formatDate(version.created_at)}
                          </span>
                          <span className="flex items-center gap-1">
                            <User className="w-3 h-3" />
                            {version.created_by}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Change reason */}
                  {version.change_reason && (
                    <div className="mb-3 text-sm text-gray-700">
                      <span className="font-medium">Reason:</span> {version.change_reason}
                    </div>
                  )}

                  {/* Steps preview */}
                  <div className="mb-3 text-sm">
                    <span className="font-medium text-gray-700">Steps:</span>
                    <span className="ml-2 text-gray-600">
                      {version.steps.length} step{version.steps.length !== 1 ? 's' : ''}
                    </span>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => onViewVersion && onViewVersion(version)}
                      className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 flex items-center gap-1.5 transition-colors"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      View
                    </button>
                    
                    {version.version_number !== currentVersion && (
                      <button
                        onClick={() => onRollback && onRollback(version.id)}
                        className="px-3 py-1.5 text-sm bg-orange-100 text-orange-700 rounded hover:bg-orange-200 flex items-center gap-1.5 transition-colors"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        Rollback
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-4 bg-gray-50">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>
              {versions.length} version{versions.length !== 1 ? 's' : ''} total
            </span>
            <span>
              {selectedVersions.length > 0 && (
                <span className="text-blue-600 font-medium">
                  {selectedVersions.length} selected for comparison
                </span>
              )}
            </span>
          </div>
        </div>
      </div>
    </>
  );
};

export default VersionHistoryPanel;
