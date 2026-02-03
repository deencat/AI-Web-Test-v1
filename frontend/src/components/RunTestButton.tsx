import { useState } from 'react';
import { Button } from './common/Button';
import executionService from '../services/executionService';
import browserProfileService from '../services/browserProfileService';
import { Upload } from 'lucide-react';

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
  const [profileFile, setProfileFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleRunTest = async (withProfile: boolean = false) => {
    setIsRunning(true);

    try {
      let browserProfileData = undefined;

      // Upload profile if provided
      if (withProfile && profileFile) {
        setUploading(true);
        try {
          const uploadResponse = await browserProfileService.uploadProfile(profileFile);
          browserProfileData = uploadResponse.profile_data;
          console.log('Profile uploaded successfully:', uploadResponse);
        } catch (error) {
          console.error('Failed to upload profile:', error);
          alert('Failed to upload browser profile. Running test without profile.');
        } finally {
          setUploading(false);
        }
      }

      const response = await executionService.startExecution(testCaseId, {
        browser: 'chromium',
        environment: 'dev',
        base_url: 'https://web.three.com.hk', // Base domain (actual URL from test steps)
        triggered_by: 'manual',
        browser_profile_data: browserProfileData,
      });

      // Show success notification
      console.log(`Test ${testCaseName || testCaseId} queued for execution`, response);
      
      if (browserProfileData) {
        console.log('Test will run with browser profile session data');
      }

      // Notify parent component
      if (onExecutionStart) {
        onExecutionStart(response.id);
      }

      // Close dialog and reset
      setShowProfileDialog(false);
      setProfileFile(null);

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
    } else {
      handleRunTest(false);
    }
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
            {uploading ? 'Uploading Profile...' : 'Queuing...'}
          </>
        ) : (
          <>
            <span className="mr-2">▶</span>
            Run Test
          </>
        )}
      </Button>

      {/* Profile Upload Dialog */}
      {showProfileDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">
              Browser Profile (Optional)
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Upload a browser profile ZIP to run this test with pre-authenticated session (cookies, localStorage, etc.)
            </p>

            {/* File Upload */}
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                Profile ZIP File
              </label>
              <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-4 text-center">
                {profileFile ? (
                  <div>
                    <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                      {profileFile.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {(profileFile.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                ) : (
                  <div>
                    <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Drag & drop or click to upload
                    </p>
                  </div>
                )}
                <label className="cursor-pointer">
                  <span className="text-blue-600 hover:text-blue-700 text-sm">
                    {profileFile ? 'Change File' : 'Browse Files'}
                  </span>
                  <input
                    type="file"
                    accept=".zip"
                    className="hidden"
                    onChange={(e) => e.target.files && setProfileFile(e.target.files[0])}
                  />
                </label>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <Button
                onClick={() => handleRunTest(true)}
                disabled={isRunning || !profileFile}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white disabled:opacity-50"
              >
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
                  setProfileFile(null);
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

