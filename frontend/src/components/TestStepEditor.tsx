import React, { useState, useEffect, useCallback } from 'react';
import { debounce } from 'lodash';
import { LoopBlockEditor, LoopBlock } from './LoopBlockEditor';

interface TestStepEditorProps {
  testId: number;
  initialSteps: string;
  initialVersion?: number;
  loopBlocks?: LoopBlock[];
  onSave?: (versionNumber: number) => void;
  onLoopBlocksChange?: (loopBlocks: LoopBlock[]) => void;
}

interface SaveResponse {
  id: number;
  current_version?: number;
  title?: string;
  [key: string]: any;
}

export const TestStepEditor: React.FC<TestStepEditorProps> = ({
  testId,
  initialSteps,
  initialVersion = 1,
  loopBlocks = [],
  onSave,
  onLoopBlocksChange
}) => {
  const [steps, setSteps] = useState(initialSteps);
  const [savedSteps, setSavedSteps] = useState(initialSteps); // Track last saved content
  const [currentVersion, setCurrentVersion] = useState(initialVersion);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showLoopBlocks, setShowLoopBlocks] = useState(true);
  const [localLoopBlocks, setLocalLoopBlocks] = useState<LoopBlock[]>(loopBlocks);

  // Auto-save function (debounced)
  const autoSave = useCallback(
    debounce(async (content: string, lastSavedContent: string) => {
      if (content === lastSavedContent || content.trim() === '') {
        // No changes or empty content, skip save
        console.log('⏭️ Auto-save skipped - no changes');
        return;
      }

      console.log('💾 Auto-saving...');
      setIsSaving(true);
      setError(null);

      try {
        const token = localStorage.getItem('token');
        if (!token) {
          throw new Error('Not authenticated');
        }

        const response = await fetch(`http://localhost:8000/api/v1/tests/${testId}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            steps: content.split('\n').filter(line => line.trim() !== ''),
            test_data: {
              loop_blocks: localLoopBlocks
            }
          })
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `Save failed: ${response.statusText}`);
        }

        const data: SaveResponse = await response.json();
        setCurrentVersion(data.current_version || currentVersion);
        setSavedSteps(content); // Update saved baseline
        setLastSaved(new Date());
        console.log('✅ Auto-save complete - version', data.current_version);
        
        if (onSave) {
          onSave(data.current_version || currentVersion);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to save');
        console.error('Auto-save error:', err);
      } finally {
        setIsSaving(false);
      }
    }, 2000), // 2-second debounce
    [testId, onSave]
  );

  // Handle text change
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newContent = e.target.value;
    setSteps(newContent);
    autoSave(newContent, savedSteps); // Compare with last saved content
  };

  // Manual save function
  const handleManualSave = async () => {
    if (steps === savedSteps) {
      console.log('⏭️ Manual save skipped - no changes');
      return; // No changes
    }

    console.log('💾 Manual saving...');
    setIsSaving(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(`http://localhost:8000/api/v1/tests/${testId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          steps: steps.split('\n').filter(line => line.trim() !== ''),
          test_data: {
            loop_blocks: localLoopBlocks
          }
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Save failed: ${response.statusText}`);
      }

      const data: SaveResponse = await response.json();
      setCurrentVersion(data.current_version || currentVersion);
      setSavedSteps(steps); // Update saved baseline
      setLastSaved(new Date());
      console.log('✅ Manual save complete - version', data.current_version);
      
      if (onSave) {
        onSave(data.current_version || currentVersion);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save');
      console.error('Manual save error:', err);
    } finally {
      setIsSaving(false);
    }
  };

  // Calculate "last saved" time ago
  const getTimeSince = () => {
    if (!lastSaved) return null;
    
    const seconds = Math.floor((Date.now() - lastSaved.getTime()) / 1000);
    
    if (seconds < 60) return `${seconds} seconds ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
    return `${Math.floor(seconds / 86400)} days ago`;
  };

  // Update time display every 10 seconds
  const [, setTick] = useState(0);
  useEffect(() => {
    const interval = setInterval(() => {
      setTick(t => t + 1);
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="test-step-editor">
      {/* Loop Block Editor */}
      <LoopBlockEditor
        totalSteps={steps.split('\n').filter(line => line.trim() !== '').length}
        loopBlocks={localLoopBlocks}
        onChange={(newLoopBlocks) => {
          setLocalLoopBlocks(newLoopBlocks);
          if (onLoopBlocksChange) {
            onLoopBlocksChange(newLoopBlocks);
          }
        }}
      />

      {/* Loop Blocks Display */}
      {loopBlocks && loopBlocks.length > 0 && (
        <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-sm font-semibold text-blue-800">
              🔁 Loop Blocks ({loopBlocks.length})
            </h3>
            <button
              onClick={() => setShowLoopBlocks(!showLoopBlocks)}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              {showLoopBlocks ? '▼ Collapse' : '▶ Expand'}
            </button>
          </div>
          
          {showLoopBlocks && (
            <div className="space-y-2">
              {loopBlocks.map((loop) => (
                <div key={loop.id} className="bg-white p-3 rounded border border-blue-200">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="font-medium text-sm text-gray-800">
                        {loop.description}
                      </div>
                      <div className="mt-1 text-xs text-gray-600">
                        <span className="inline-block mr-3">
                          📍 Steps: {loop.start_step}-{loop.end_step}
                        </span>
                        <span className="inline-block mr-3">
                          🔢 Iterations: {loop.iterations}
                        </span>
                        {loop.variables && Object.keys(loop.variables).length > 0 && (
                          <span className="inline-block">
                            🔀 Variables: {Object.keys(loop.variables).length}
                          </span>
                        )}
                      </div>
                      {loop.variables && Object.keys(loop.variables).length > 0 && (
                        <div className="mt-2 text-xs bg-gray-50 p-2 rounded font-mono">
                          {Object.entries(loop.variables).map(([key, value]) => (
                            <div key={key} className="text-gray-700">
                              {key}: <span className="text-blue-600">{value}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="ml-3 px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded">
                      {loop.id}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          <div className="mt-3 text-xs text-gray-600">
            <span className="mr-2">ℹ️</span>
            Loop blocks repeat step sequences automatically without duplication.
          </div>
        </div>
      )}
      
      {/* Header with version and save button */}
      <div className="flex justify-between items-center mb-2">
        <label className="block text-sm font-medium text-gray-700">
          Test Steps {currentVersion > 0 && (
            <span className="ml-2 text-xs text-gray-500">(v{currentVersion})</span>
          )}
        </label>
        
        <button
          onClick={handleManualSave}
          disabled={isSaving || steps === savedSteps}
          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {isSaving ? 'Saving...' : 'Save Now'}
        </button>
      </div>

      {/* Textarea */}
      <textarea
        value={steps}
        onChange={handleChange}
        className="w-full h-64 p-3 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        placeholder="Enter test steps (one per line):&#10;&#10;1. Navigate to https://example.com&#10;2. Click on 'Login' button&#10;3. Enter username: admin&#10;4. Enter password: ****&#10;5. Click 'Submit'&#10;6. Verify dashboard loads&#10;&#10;Expected Result:&#10;- User successfully logged in&#10;- Dashboard displays with welcome message"
      />

      {/* Status footer */}
      <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
        <div>
          {isSaving && (
            <span className="text-blue-600">
              💾 Saving...
            </span>
          )}
          {!isSaving && lastSaved && (
            <span className="text-green-600">
              ✓ Saved {getTimeSince()}
            </span>
          )}
          {!isSaving && !lastSaved && (
            <span>
              ⓘ Changes auto-saved 2 seconds after typing
            </span>
          )}
        </div>
        
        {error && (
          <span className="text-red-600">
            ⚠️ Error: {error}
          </span>
        )}
      </div>
    </div>
  );
};

export default TestStepEditor;
