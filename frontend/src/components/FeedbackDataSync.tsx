/**
 * Feedback Data Sync Component
 * Sprint 4 Feature: Team Collaboration via Feedback Import/Export
 * 
 * Allows developers to sync feedback data across different databases
 * by exporting to JSON and importing from JSON files.
 * 
 * Security Features:
 * - URL sanitization (removes query params)
 * - HTML snapshot exclusion
 * - User ID to email mapping
 * - Duplicate detection via hash
 * - Input validation
 */

import React, { useState, useRef } from 'react';
import { Card } from './common/Card';
import { Button } from './common/Button';
import feedbackService, {
  FeedbackExportParams,
  FeedbackImportResult,
} from '../services/feedbackService';

export function FeedbackDataSync() {
  // Export state
  const [isExporting, setIsExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  // Import state
  const [isImporting, setIsImporting] = useState(false);
  const [importSuccess, setImportSuccess] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const [importResult, setImportResult] = useState<FeedbackImportResult | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [mergeStrategy, setMergeStrategy] = useState<'skip_duplicates' | 'update_existing' | 'create_all'>('skip_duplicates');
  const [showImportDialog, setShowImportDialog] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Export handler
  const handleExport = async () => {
    try {
      setIsExporting(true);
      setExportSuccess(false);
      setExportError(null);

      const params: FeedbackExportParams = {
        include_html: false, // Security: exclude HTML snapshots
        include_screenshots: true,
        limit: 1000,
      };

      const blob = await feedbackService.exportFeedback(params);
      
      // Trigger download
      const filename = `feedback-export-${new Date().toISOString().split('T')[0]}.json`;
      feedbackService.downloadExportFile(blob, filename);

      setExportSuccess(true);
      setTimeout(() => setExportSuccess(false), 5000);
    } catch (error: any) {
      setExportError(error.response?.data?.detail || error.message || 'Export failed');
    } finally {
      setIsExporting(false);
    }
  };

  // File selection handler
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (!file.name.endsWith('.json')) {
        setImportError('Please select a JSON file');
        return;
      }
      setSelectedFile(file);
      setShowImportDialog(true);
      setImportError(null);
    }
  };

  // Import handler
  const handleImport = async () => {
    if (!selectedFile) return;

    try {
      setIsImporting(true);
      setImportSuccess(false);
      setImportError(null);
      setImportResult(null);

      const result = await feedbackService.importFeedback(selectedFile, mergeStrategy);
      
      setImportResult(result);
      setImportSuccess(true);
      setShowImportDialog(false);
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      setSelectedFile(null);
    } catch (error: any) {
      setImportError(error.response?.data?.detail || error.message || 'Import failed');
    } finally {
      setIsImporting(false);
    }
  };

  const handleDialogClose = () => {
    setShowImportDialog(false);
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-6">
      {/* Security Notice */}
      <Card>
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center mt-1">
            <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Security Features</h3>
            <ul className="text-sm text-gray-700 space-y-1 list-disc list-inside">
              <li>URLs are sanitized (query parameters removed)</li>
              <li>HTML snapshots are excluded from export</li>
              <li>User IDs are mapped to emails</li>
              <li>Duplicate detection via content hash</li>
              <li>Foreign key references are removed for portability</li>
              <li>File type and JSON structure validation</li>
              <li>Import operations are logged with audit trail</li>
            </ul>
          </div>
        </div>
      </Card>

      {/* Export Section */}
      <Card>
        <h2 className="text-xl font-bold text-gray-900 mb-4">Export Feedback Data</h2>
        <p className="text-gray-700 mb-4">
          Export all feedback data to a JSON file. This file can be shared with other team members
          who can import it into their local database.
        </p>

        <div className="space-y-4">
          <Button
            variant="primary"
            onClick={handleExport}
            loading={isExporting}
            disabled={isExporting}
            className="flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
            {isExporting ? 'Exporting...' : 'Export to JSON'}
          </Button>

          {exportSuccess && (
            <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg">
              <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span className="text-green-800 font-medium">Export successful! File downloaded.</span>
            </div>
          )}

          {exportError && (
            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
              <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span className="text-red-800 font-medium">{exportError}</span>
            </div>
          )}
        </div>
      </Card>

      {/* Import Section */}
      <Card>
        <h2 className="text-xl font-bold text-gray-900 mb-4">Import Feedback Data</h2>
        <p className="text-gray-700 mb-4">
          Import feedback data from a JSON file exported by another team member.
          Duplicates will be automatically detected and handled based on your merge strategy.
        </p>

        <div className="space-y-4">
          <input
            ref={fileInputRef}
            type="file"
            accept=".json,application/json"
            onChange={handleFileSelect}
            className="hidden"
            id="import-file-input"
          />
          
          <label htmlFor="import-file-input">
            <Button
              variant="secondary"
              className="flex items-center gap-2"
              onClick={() => fileInputRef.current?.click()}
              type="button"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
              </svg>
              Select JSON File
            </Button>
          </label>

          {importSuccess && importResult && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-2 mb-3">
                <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <h3 className="text-lg font-semibold text-green-800">Import Successful</h3>
              </div>
              
              <div className="space-y-2 text-sm text-gray-700">
                <div className="flex justify-between">
                  <span>Total processed:</span>
                  <span className="font-semibold">{importResult.total_processed}</span>
                </div>
                <div className="flex justify-between">
                  <span>Newly imported:</span>
                  <span className="font-semibold text-green-700">{importResult.imported_count}</span>
                </div>
                <div className="flex justify-between">
                  <span>Duplicates skipped:</span>
                  <span className="font-semibold text-blue-700">{importResult.skipped_count}</span>
                </div>
                <div className="flex justify-between">
                  <span>Updated:</span>
                  <span className="font-semibold text-yellow-700">{importResult.updated_count}</span>
                </div>
                {importResult.failed_count > 0 && (
                  <div className="flex justify-between">
                    <span>Failed:</span>
                    <span className="font-semibold text-red-700">{importResult.failed_count}</span>
                  </div>
                )}
              </div>

              {importResult.errors && importResult.errors.length > 0 && (
                <div className="mt-3 pt-3 border-t border-green-200">
                  <h4 className="font-semibold text-gray-900 mb-2">Errors:</h4>
                  <ul className="space-y-1 text-sm text-gray-700">
                    {importResult.errors.map((err: string, idx: number) => (
                      <li key={idx} className="text-red-700">
                        {err}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {importError && (
            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
              <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span className="text-red-800 font-medium">{importError}</span>
            </div>
          )}
        </div>
      </Card>

      {/* Import Preview Dialog */}
      {showImportDialog && selectedFile && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-gray-900">Import Preview</h2>
            </div>
            
            <div className="p-6 space-y-4">
              <div>
                <p className="text-sm text-gray-600 mb-1">File:</p>
                <p className="font-semibold text-gray-900">{selectedFile.name}</p>
                <p className="text-sm text-gray-500">Size: {(selectedFile.size / 1024).toFixed(2)} KB</p>
              </div>

              <div className="border-t border-gray-200 pt-4">
                <label className="block text-sm font-semibold text-gray-900 mb-3">
                  Merge Strategy
                </label>
                <div className="space-y-2">
                  <label className="flex items-center gap-3 p-3 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50">
                    <input
                      type="radio"
                      name="merge-strategy"
                      value="skip_duplicates"
                      checked={mergeStrategy === 'skip_duplicates'}
                      onChange={(e) => setMergeStrategy(e.target.value as any)}
                      className="w-4 h-4 text-blue-600"
                    />
                    <div>
                      <div className="font-medium text-gray-900">Skip Duplicates (Recommended)</div>
                      <div className="text-sm text-gray-600">Only import new feedback, skip existing ones</div>
                    </div>
                  </label>

                  <label className="flex items-center gap-3 p-3 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50">
                    <input
                      type="radio"
                      name="merge-strategy"
                      value="update_existing"
                      checked={mergeStrategy === 'update_existing'}
                      onChange={(e) => setMergeStrategy(e.target.value as any)}
                      className="w-4 h-4 text-blue-600"
                    />
                    <div>
                      <div className="font-medium text-gray-900">Update Existing</div>
                      <div className="text-sm text-gray-600">Update existing feedback with new data</div>
                    </div>
                  </label>

                  <label className="flex items-center gap-3 p-3 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50">
                    <input
                      type="radio"
                      name="merge-strategy"
                      value="create_all"
                      checked={mergeStrategy === 'create_all'}
                      onChange={(e) => setMergeStrategy(e.target.value as any)}
                      className="w-4 h-4 text-blue-600"
                    />
                    <div>
                      <div className="font-medium text-gray-900">Create All (Allow Duplicates)</div>
                      <div className="text-sm text-gray-600">Import everything, even if duplicates exist</div>
                    </div>
                  </label>
                </div>
              </div>
            </div>

            <div className="p-6 border-t border-gray-200 flex justify-end gap-3">
              <Button
                variant="secondary"
                onClick={handleDialogClose}
                disabled={isImporting}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleImport}
                loading={isImporting}
                disabled={isImporting}
              >
                {isImporting ? 'Importing...' : 'Import'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
