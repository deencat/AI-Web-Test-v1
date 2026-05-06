/**
 * RenameModuleModal — Sprint 10.11 (Option C: Preview + Confirm Cascade)
 *
 * Shows a two-step rename flow:
 *  1. User types the new slug and clicks "Preview"
 *  2. Backend dry-run lists affected test cases
 *  3. User reviews and clicks "Confirm Rename" (or Cancel)
 *
 * On confirm, PUT /{id} is called which atomically renames the module
 * and cascades @module:old_name → @module:new_name in all affected tests.
 */
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import stepLibraryService from '../services/stepLibraryService';
import type { StepLibraryModule } from '../types/stepLibrary.types';

interface AffectedTestCase {
  id: number;
  name: string;
}

interface Props {
  module: StepLibraryModule;
  onClose: () => void;
  /** Called with the updated module and count of test cases rewritten. */
  onRenamed: (updated: StepLibraryModule, updatedCount: number) => void;
}

type Phase = 'input' | 'previewing' | 'previewed' | 'confirming';

export function RenameModuleModal({ module, onClose, onRenamed }: Props) {
  const [newName, setNewName] = useState(module.name);
  const [phase, setPhase] = useState<Phase>('input');
  const [affected, setAffected] = useState<AffectedTestCase[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function handlePreview() {
    if (!newName.trim()) {
      setError('New name is required.');
      return;
    }
    setError(null);
    setPhase('previewing');
    try {
      const result = await stepLibraryService.renamePreview(module.id, newName.trim());
      setAffected(result.affected_test_cases);
      setPhase('previewed');
    } catch {
      setError('Failed to fetch preview. Please try again.');
      setPhase('input');
    }
  }

  async function handleConfirm() {
    setError(null);
    setPhase('confirming');
    try {
      const updated = await stepLibraryService.update(module.id, { name: newName.trim() });
      onRenamed(updated, affected.length);
    } catch {
      setError('Rename failed. The name may already be taken.');
      setPhase('previewed');
    }
  }

  const isPreviewing = phase === 'previewing' || phase === 'confirming';

  return (
    <div
      className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="rename-modal-title"
    >
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg">
        <div className="p-6">
          <h2 id="rename-modal-title" className="text-xl font-semibold mb-1">
            Rename Module
          </h2>
          <p className="text-sm text-gray-500 mb-4">
            Current slug:{' '}
            <code className="bg-gray-100 px-1 rounded font-mono">{module.name}</code>
          </p>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded text-sm">
              {error}
            </div>
          )}

          <div className="mb-4">
            <label
              htmlFor="rename-new-name"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              New name
            </label>
            <input
              id="rename-new-name"
              type="text"
              value={newName}
              onChange={e => {
                setNewName(e.target.value);
                // Reset to input phase when user edits after a preview
                if (phase === 'previewed') setPhase('input');
              }}
              disabled={isPreviewing}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 font-mono text-sm disabled:bg-gray-50"
              aria-label="New name"
            />
          </div>

          {/* Preview results */}
          {(phase === 'previewed' || phase === 'confirming') && (
            <div className="mb-4 border border-gray-200 rounded p-3 bg-gray-50">
              {affected.length === 0 ? (
                <p className="text-sm text-gray-600">
                  No test cases reference <code>@module:{module.name}</code> — safe to rename.
                </p>
              ) : (
                <>
                  <p className="text-sm font-medium text-gray-700 mb-2">
                    {affected.length} test case{affected.length !== 1 ? 's' : ''} will be updated:
                  </p>
                  <ul className="space-y-1 max-h-40 overflow-y-auto">
                    {affected.map(tc => (
                      <li key={tc.id} className="text-sm">
                        <Link
                          to={`/tests/${tc.id}`}
                          className="text-blue-600 hover:underline"
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {tc.name}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 mt-2">
            <button
              onClick={onClose}
              disabled={isPreviewing}
              className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>

            {phase !== 'previewed' && phase !== 'confirming' && (
              <button
                onClick={handlePreview}
                disabled={isPreviewing || !newName.trim()}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {phase === 'previewing' ? 'Checking…' : 'Preview'}
              </button>
            )}

            {(phase === 'previewed' || phase === 'confirming') && (
              <>
                <button
                  onClick={() => setPhase('input')}
                  disabled={isPreviewing}
                  className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
                >
                  Back
                </button>
                <button
                  onClick={handleConfirm}
                  disabled={phase === 'confirming'}
                  className="px-4 py-2 text-sm bg-orange-600 text-white rounded hover:bg-orange-700 disabled:opacity-50"
                >
                  {phase === 'confirming' ? 'Renaming…' : 'Confirm Rename'}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
