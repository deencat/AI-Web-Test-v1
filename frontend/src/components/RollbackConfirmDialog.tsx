import React, { useState } from 'react';
import { AlertTriangle, RotateCcw, X } from 'lucide-react';

interface Version {
  id: number;
  version_number: number;
  created_at: string;
  created_by: string;
  change_reason?: string;
}

interface RollbackConfirmDialogProps {
  testId: number;
  version: Version;
  currentVersion: number;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (reason: string) => Promise<void>;
}

export const RollbackConfirmDialog: React.FC<RollbackConfirmDialogProps> = ({
  testId,
  version,
  currentVersion,
  isOpen,
  onClose,
  onConfirm
}) => {
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleConfirm = async () => {
    if (!reason.trim()) {
      setError('Please provide a reason for the rollback');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await onConfirm(reason.trim());
      // Reset form on success
      setReason('');
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to rollback version');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setReason('');
      setError(null);
      onClose();
    }
  };

  if (!isOpen) return null;

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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Dialog */}
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md z-50 m-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <RotateCcw className="w-6 h-6 text-orange-600" />
            <h2 className="text-xl font-bold text-gray-900">Rollback to Version</h2>
          </div>
          <button
            onClick={handleClose}
            disabled={loading}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
            aria-label="Close"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Warning */}
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-orange-900 mb-1">
                  This will create a new version
                </p>
                <p className="text-sm text-orange-800">
                  Rolling back to version {version.version_number} will create a new version (v{currentVersion + 1}) 
                  with the content from version {version.version_number}. Your current version (v{currentVersion}) 
                  will be preserved in history.
                </p>
              </div>
            </div>
          </div>

          {/* Version Info */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Target Version:</span>
              <span className="text-sm font-semibold text-gray-900">v{version.version_number}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Created:</span>
              <span className="text-sm text-gray-600">{formatDate(version.created_at)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">By:</span>
              <span className="text-sm text-gray-600">{version.created_by}</span>
            </div>
            {version.change_reason && (
              <div className="pt-2 border-t border-gray-200">
                <span className="text-sm font-medium text-gray-700">Original Reason:</span>
                <p className="text-sm text-gray-600 mt-1">{version.change_reason}</p>
              </div>
            )}
          </div>

          {/* Current Version Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-blue-700">Current Version:</span>
              <span className="text-sm font-semibold text-blue-900">v{currentVersion}</span>
            </div>
          </div>

          {/* Reason Input */}
          <div>
            <label htmlFor="rollback-reason" className="block text-sm font-medium text-gray-700 mb-2">
              Reason for Rollback <span className="text-red-500">*</span>
            </label>
            <textarea
              id="rollback-reason"
              value={reason}
              onChange={(e) => {
                setReason(e.target.value);
                setError(null);
              }}
              placeholder="e.g., Previous version had better test coverage, or Reverting due to test failures"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
              disabled={loading}
            />
            <p className="mt-1 text-xs text-gray-500">
              This reason will be saved with the new version created from the rollback.
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200">
          <button
            onClick={handleClose}
            disabled={loading}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={loading || !reason.trim()}
            className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Rolling back...</span>
              </>
            ) : (
              <>
                <RotateCcw className="w-4 h-4" />
                <span>Confirm Rollback</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

