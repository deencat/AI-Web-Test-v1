import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { RunTestButton } from '../components/RunTestButton';
import { TestStepEditor } from '../components/TestStepEditor';
import { LoopBlock } from '../components/LoopBlockEditor';
import { VersionHistoryPanel } from '../components/VersionHistoryPanel';
import { VersionCompareDialog } from '../components/VersionCompareDialog';
import { RollbackConfirmDialog } from '../components/RollbackConfirmDialog';
import testsService from '../services/testsService';
import { Loader2, ArrowLeft, Calendar, User, Clock, History } from 'lucide-react';

interface TestDetail {
  id: string | number;
  title?: string;
  name?: string;
  description: string;
  test_type?: string;
  priority: 'high' | 'medium' | 'low';
  status: 'passed' | 'failed' | 'pending' | 'running';
  steps?: string[] | string;
  expected_result?: string;
  created_at: string;
  updated_at: string;
  created_by?: string;
  current_version?: number;
  test_data?: {
    loop_blocks?: LoopBlock[];
    [key: string]: any;
  };
}

export const TestDetailPage: React.FC = () => {
  const { testId } = useParams<{ testId: string }>();
  const navigate = useNavigate();
  const [test, setTest] = useState<TestDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showVersionHistory, setShowVersionHistory] = useState(false);
  const [showCompareDialog, setShowCompareDialog] = useState(false);
  const [showRollbackDialog, setShowRollbackDialog] = useState(false);
  const [compareVersion1, setCompareVersion1] = useState<number | null>(null);
  const [compareVersion2, setCompareVersion2] = useState<number | null>(null);
  const [rollbackVersion, setRollbackVersion] = useState<any | null>(null);

  useEffect(() => {
    loadTestDetails();
  }, [testId]);

  const loadTestDetails = async () => {
    if (!testId) return;

    setLoading(true);
    setError(null);

    try {
      const testData = await testsService.getTestById(testId);
      setTest(testData as TestDetail);
    } catch (err) {
      console.error('Failed to load test details:', err);
      setError(err instanceof Error ? err.message : 'Failed to load test details');
    } finally {
      setLoading(false);
    }
  };

  const handleExecutionStart = (executionId: number) => {
    navigate(`/executions/${executionId}`);
  };

  const handleBack = () => {
    navigate('/tests');
  };

  const handleCompareVersions = (v1: number, v2: number) => {
    setCompareVersion1(v1);
    setCompareVersion2(v2);
    setShowCompareDialog(true);
  };

  const handleRollback = async (version: any) => {
    setRollbackVersion(version);
    setShowRollbackDialog(true);
  };

  const handleRollbackConfirm = async (reason: string) => {
    if (!test || !rollbackVersion) return;

    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('Not authenticated');
    }

    const testIdNum = typeof test.id === 'string' ? parseInt(test.id) : test.id;

    const response = await fetch(
      `http://localhost:8000/api/v1/tests/${testIdNum}/versions/rollback`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          version_id: rollbackVersion.id,
          created_by: 'user' // TODO: Get from auth context
        })
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to rollback version');
    }

    const newVersion = await response.json();
    
    // Refresh test data to show new version
    await loadTestDetails();
    
    // Close dialogs
    setShowRollbackDialog(false);
    setShowVersionHistory(false);
    setRollbackVersion(null);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-700';
      case 'medium':
        return 'bg-yellow-100 text-yellow-700';
      case 'low':
        return 'bg-green-100 text-green-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'passed':
        return 'bg-green-100 text-green-700';
      case 'failed':
        return 'bg-red-100 text-red-700';
      case 'running':
        return 'bg-blue-100 text-blue-700';
      default:
        return 'bg-yellow-100 text-yellow-700';
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="space-y-6">
          <Button variant="secondary" onClick={handleBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Tests
          </Button>
          <Card>
            <div className="text-center py-8">
              <p className="text-red-600 mb-4">{error}</p>
              <Button variant="primary" onClick={loadTestDetails}>
                Retry
              </Button>
            </div>
          </Card>
        </div>
      </Layout>
    );
  }

  if (!test) {
    return (
      <Layout>
        <div className="space-y-6">
          <Button variant="secondary" onClick={handleBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Tests
          </Button>
          <Card>
            <div className="text-center py-8">
              <p className="text-gray-600">Test not found</p>
            </div>
          </Card>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <Button variant="secondary" onClick={handleBack} className="mb-4">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Tests
            </Button>
            <h1 className="text-3xl font-bold text-gray-900">{test.title || test.name}</h1>
            <p className="text-gray-600 mt-2">{test.description}</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => setShowVersionHistory(true)}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center gap-2 transition-colors"
            >
              <History className="w-4 h-4" />
              View History
            </button>
            <RunTestButton
              testCaseId={typeof test.id === 'string' ? parseInt(test.id) : test.id}
              testCaseName={test.title || test.name}
              onExecutionStart={handleExecutionStart}
            />
          </div>
        </div>

        {/* Test Metadata */}
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Test Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-600 mb-1">Test ID</p>
              <p className="font-semibold text-gray-900">#{test.id}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Type</p>
              <span className="inline-block px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium capitalize">
                {test.test_type}
              </span>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Priority</p>
              <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium capitalize ${getPriorityColor(test.priority)}`}>
                {test.priority}
              </span>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Status</p>
              <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium capitalize ${getStatusColor(test.status)}`}>
                {test.status}
              </span>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 pt-4 border-t border-gray-200">
            <div className="flex items-center gap-2 text-gray-600">
              <Calendar className="w-4 h-4" />
              <div>
                <p className="text-xs">Created</p>
                <p className="text-sm font-medium">
                  {new Date(test.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-gray-600">
              <Clock className="w-4 h-4" />
              <div>
                <p className="text-xs">Updated</p>
                <p className="text-sm font-medium">
                  {new Date(test.updated_at).toLocaleDateString()}
                </p>
              </div>
            </div>
            {test.created_by && (
              <div className="flex items-center gap-2 text-gray-600">
                <User className="w-4 h-4" />
                <div>
                  <p className="text-xs">Created By</p>
                  <p className="text-sm font-medium">{test.created_by}</p>
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Test Steps */}
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Test Steps</h2>
          {test.id && (
            <TestStepEditor
              testId={typeof test.id === 'string' ? parseInt(test.id) : test.id}
              initialSteps={Array.isArray(test.steps) ? test.steps.join('\n') : (test.steps || '')}
              initialVersion={test.current_version || 1}
              loopBlocks={test.test_data?.loop_blocks || []}
              onSave={(versionNumber) => {
                console.log('New version saved:', versionNumber);
                // Update test data to reflect new version
                setTest({ ...test, current_version: versionNumber });
              }}
              onLoopBlocksChange={(newLoopBlocks) => {
                console.log('Loop blocks updated:', newLoopBlocks);
                // Update test data with new loop blocks
                setTest({
                  ...test,
                  test_data: {
                    ...test.test_data,
                    loop_blocks: newLoopBlocks
                  }
                });
              }}
            />
          )}
        </Card>

        {/* Expected Result */}
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Expected Result</h2>
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-gray-900 whitespace-pre-wrap">{test.expected_result}</p>
          </div>
        </Card>

        {/* Actions */}
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Actions</h2>
          <div className="flex gap-3">
            <Button
              variant="primary"
              onClick={() => navigate(`/tests?edit=${test.id}`)}
            >
              Edit Test
            </Button>
            <Button
              variant="secondary"
              onClick={async () => {
                if (window.confirm('Are you sure you want to delete this test?')) {
                  try {
                    await testsService.deleteTest(test.id.toString());
                    alert('Test deleted successfully!');
                    navigate('/tests');
                  } catch (error) {
                    alert(error instanceof Error ? error.message : 'Failed to delete test');
                  }
                }
              }}
              className="text-red-600 hover:text-red-700"
            >
              Delete Test
            </Button>
          </div>
        </Card>
      </div>

      {/* Version History Panel */}
      {test && (
        <VersionHistoryPanel
          testId={typeof test.id === 'string' ? parseInt(test.id) : test.id}
          currentVersion={test.current_version || 1}
          isOpen={showVersionHistory}
          onClose={() => setShowVersionHistory(false)}
          onViewVersion={(version) => {
            console.log('View version:', version);
            // TODO: Implement view version dialog (optional feature)
          }}
          onCompareVersions={handleCompareVersions}
          onRollback={handleRollback}
        />
      )}

      {/* Version Compare Dialog */}
      {test && compareVersion1 && compareVersion2 && (
        <VersionCompareDialog
          testId={typeof test.id === 'string' ? parseInt(test.id) : test.id}
          versionId1={compareVersion1}
          versionId2={compareVersion2}
          isOpen={showCompareDialog}
          onClose={() => {
            setShowCompareDialog(false);
            setCompareVersion1(null);
            setCompareVersion2(null);
          }}
        />
      )}

      {/* Rollback Confirm Dialog */}
      {test && rollbackVersion && (
        <RollbackConfirmDialog
          testId={typeof test.id === 'string' ? parseInt(test.id) : test.id}
          version={rollbackVersion}
          currentVersion={test.current_version || 1}
          isOpen={showRollbackDialog}
          onClose={() => {
            setShowRollbackDialog(false);
            setRollbackVersion(null);
          }}
          onConfirm={handleRollbackConfirm}
        />
      )}
    </Layout>
  );
};
