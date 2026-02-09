import { useEffect, useState } from 'react';
import { Button } from './common/Button';
import executionService from '../services/executionService';
import browserProfileService from '../services/browserProfileService';
import { Lock, RefreshCw } from 'lucide-react';
import type { BrowserProfile } from '../types/browserProfile';

interface RunTestButtonProps {
  testCaseId: number;
  testCaseName?: string;
  onExecutionStart?: (executionId: number) => void;
  disabled?: boolean;
  className?: string;
  enableProfileUpload?: boolean; // New prop
}

export function RunTestButton({
  testCaseId,
  testCaseName,
  onExecutionStart,
  disabled = false,
  className = '',
  enableProfileUpload = false,
}: RunTestButtonProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [showProfileDialog, setShowProfileDialog] = useState(false);
  const [profiles, setProfiles] = useState<BrowserProfile[]>([]);
  const [profilesLoading, setProfilesLoading] = useState(false);
  const [selectedProfileId, setSelectedProfileId] = useState<number | null>(null);

  const loadProfiles = async () => {
    try {
      setProfilesLoading(true);
      const response = await browserProfileService.getAllProfiles();
      setProfiles(response.profiles);
    } catch (error) {
      console.error('Failed to load browser profiles:', error);
    } finally {
      setProfilesLoading(false);
    }
  };

  useEffect(() => {
    if (showProfileDialog) {
      loadProfiles();
    }
  }, [showProfileDialog]);

  const handleRunTest = async (withProfile: boolean = false) => {
    setIsRunning(true);

    try {
      const browserProfileId = withProfile ? selectedProfileId ?? undefined : undefined;

      const response = await executionService.startExecution(testCaseId, {
        browser: 'chromium',
        environment: 'dev',
        base_url: 'https://web.three.com.hk', // Base domain (actual URL from test steps)
        triggered_by: 'manual',
        browser_profile_id: browserProfileId,
      });

      // Show success notification
      console.log(`Test ${testCaseName || testCaseId} queued for execution`, response);
      
      if (browserProfileId) {
        console.log('Test will run with browser profile session data');
      }
      setSelectedProfileId(null);

      // Notify parent component
      if (onExecutionStart) {
        onExecutionStart(response.id);
      }

    // Close dialog and reset
    setShowProfileDialog(false);

      // Optional: Navigate to execution detail page
      // navigate(`/executions/${response.id}`);
    } catch (error) {
      console.error('Failed to start execution:', error);
      alert(error instanceof Error ? error.message : 'Failed to start execution');
    } finally {
      setIsRunning(false);
    }
  };

  const handleButtonClick = () => {
    if (enableProfileUpload) {
      setShowProfileDialog(true);
      return;
    }

    handleRunTest(false);
  };

  return (
    <>
      <Button
        variant="primary"
        size="md"
        onClick={handleButtonClick}
        disabled={disabled || isRunning}
        className={className}
      >
        {isRunning ? (
          <>
            <span className="inline-block animate-spin mr-2">⚙</span>
            Queuing...
          </>
        ) : (
          <>
            <span className="mr-2">▶</span>
            Run Test
          </>
        )}
      </Button>

      {/* Profile Selection Dialog */}
      {showProfileDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">
              Browser Profile (Optional)
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Select a synced browser profile to reuse cookies, localStorage, and HTTP credentials.
            </p>

            <div className="mb-4">
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                Profile Selection
              </label>
              <div className="relative">
                <select
                  value={selectedProfileId ?? ''}
                  onChange={(e) => setSelectedProfileId(e.target.value ? Number(e.target.value) : null)}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  disabled={profilesLoading}
                >
                  <option value="">-- No Profile (Fresh Browser) --</option>
                  {profiles.map((profile) => (
                    <option key={profile.id} value={profile.id}>
                      {profile.profile_name}
                      {profile.has_http_credentials ? ' 🔐' : ''}
                      {profile.has_session_data ? ' ✓' : ' ⚠️'}
                    </option>
                  ))}
                </select>
                {profilesLoading && (
                  <RefreshCw className="w-4 h-4 animate-spin absolute right-3 top-3 text-gray-400" />
                )}
              </div>

              {selectedProfileId && (
                <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-md text-xs text-blue-800 dark:text-blue-200">
                  {profiles.find((profile) => profile.id === selectedProfileId)?.has_session_data
                    ? 'Session data is synced and ready for use.'
                    : 'This profile has no synced session data yet.'}
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <Button
                onClick={() => handleRunTest(true)}
                disabled={isRunning || !selectedProfileId}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white disabled:opacity-50"
              >
                <Lock className="w-4 h-4 mr-2" />
                Run with Profile
              </Button>
              <Button
                onClick={() => handleRunTest(false)}
                disabled={isRunning}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
              >
                Run without Profile
              </Button>
              <Button
                onClick={() => {
                  setShowProfileDialog(false);
                  setSelectedProfileId(null);
                }}
                className="bg-gray-300 hover:bg-gray-400 dark:bg-gray-600 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-200"
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

