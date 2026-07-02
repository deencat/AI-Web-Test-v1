import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { TestStepEditor } from '../components/TestStepEditor';
import { InlineTitleEditor } from '../components/tests/InlineTitleEditor';
import testsService from '../services/testsService';
import executionService from '../services/executionService';
import schedulesService, { type TestSchedule, type CreateSchedulePayload } from '../services/schedulesService';
import { GeneratedTestCase } from '../types/api';
import { Loader2, Plus, Search, Trash2, Play, Eye, Edit, Clock } from 'lucide-react';

interface SavedTest {
  id: number;
  title: string;
  description: string;
  test_type: string;
  priority: 'high' | 'medium' | 'low';
  status: string;
  created_at: string;
  updated_at: string;
}

export const SavedTestsPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [tests, setTests] = useState<SavedTest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterPriority, setFilterPriority] = useState('all');
  const [filterScheduled, setFilterScheduled] = useState('all');
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [batchDeleting, setBatchDeleting] = useState(false);

  const [editingTest, setEditingTest] = useState<GeneratedTestCase | null>(null);
  const [editLoading, setEditLoading] = useState(false);
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({
    title: '',
    description: '',
    steps: [] as string[],
    expected_result: '',
    priority: 'medium' as 'high' | 'medium' | 'low',
    requires_runtime_credentials: false,
  });

  const [scheduleTarget, setScheduleTarget] = useState<{ id: number; title: string } | null>(null);
  const [existingSchedules, setExistingSchedules] = useState<TestSchedule[]>([]);
  const [loadingSchedules, setLoadingSchedules] = useState(false);
  const [scheduleType, setScheduleType] = useState<'interval' | 'cron'>('interval');
  const [intervalMinutes, setIntervalMinutes] = useState('60');
  const [cronExpression, setCronExpression] = useState('0 9 * * *');
  const [scheduleBrowser, setScheduleBrowser] = useState('chromium');
  const [scheduleEnvironment, setScheduleEnvironment] = useState('dev');
  const [savingSchedule, setSavingSchedule] = useState(false);
  const [togglingScheduleId, setTogglingScheduleId] = useState<number | null>(null);
  const [scheduledTestIds, setScheduledTestIds] = useState<Record<number, number>>({});

  useEffect(() => {
    loadTests();
    loadAllScheduleBadges();
  }, []);

  useEffect(() => {
    const editId = searchParams.get('edit');
    if (editId) {
      void loadAndEditTest(editId);
    }
  }, [searchParams]);

  const loadAllScheduleBadges = async () => {
    try {
      const all = await schedulesService.listAll();
      const counts: Record<number, number> = {};
      all.forEach((s) => {
        if (s.enabled) counts[s.test_case_id] = (counts[s.test_case_id] ?? 0) + 1;
      });
      setScheduledTestIds(counts);
    } catch {
      // non-fatal
    }
  };

  const loadTests = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await testsService.getAllTests();
      setTests(response as unknown as SavedTest[]);
    } catch (err) {
      console.error('Failed to load tests:', err);
      setError(err instanceof Error ? err.message : 'Failed to load tests');
    } finally {
      setLoading(false);
    }
  };

  const loadAndEditTest = async (testId: string) => {
    try {
      setEditLoading(true);
      setEditError(null);
      const test = await testsService.getTestById(testId);

      const testCase: GeneratedTestCase = {
        id: test.id?.toString() || testId,
        title: (test as { title?: string; name?: string }).title || (test as { name?: string }).name || '',
        description: test.description || '',
        steps: Array.isArray((test as { steps?: unknown[] }).steps)
          ? (test as { steps: unknown[] }).steps.map((step) =>
              typeof step === 'string' ? step : (step as { description?: string }).description || ''
            )
          : [],
        expected_result: (test as { expected_result?: string }).expected_result || '',
        priority: test.priority as 'high' | 'medium' | 'low',
      };

      setEditingTest(testCase);
      setEditForm({
        title: testCase.title,
        description: testCase.description,
        steps: [...testCase.steps],
        expected_result: testCase.expected_result,
        priority: testCase.priority,
        requires_runtime_credentials:
          (test as { requires_runtime_credentials?: boolean }).requires_runtime_credentials ?? false,
      });
    } catch (err) {
      console.error('Failed to load test:', err);
      setEditError(err instanceof Error ? err.message : 'Failed to load test');
      alert('Failed to load test for editing.');
      setSearchParams({}, { replace: true });
    } finally {
      setEditLoading(false);
    }
  };

  const handleSaveEdit = async () => {
    if (!editingTest) return;

    if (!editForm.title.trim()) {
      setEditError('Title is required');
      return;
    }

    try {
      setEditSaving(true);
      setEditError(null);

      await testsService.updateTest(editingTest.id!, {
        title: editForm.title,
        description: editForm.description,
        priority: editForm.priority,
        steps: editForm.steps,
        expected_result: editForm.expected_result,
        requires_runtime_credentials: editForm.requires_runtime_credentials,
      });

      setTests((prev) =>
        prev.map((t) =>
          t.id.toString() === editingTest.id
            ? {
                ...t,
                title: editForm.title,
                description: editForm.description,
                priority: editForm.priority,
              }
            : t
        )
      );

      closeEditDrawer();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update test';
      setEditError(errorMessage);
    } finally {
      setEditSaving(false);
    }
  };

  const closeEditDrawer = () => {
    setEditingTest(null);
    setEditError(null);
    setSearchParams({}, { replace: true });
  };

  const handleTitleChange = (testId: number, newTitle: string) => {
    setTests((prev) =>
      prev.map((t) => (t.id === testId ? { ...t, title: newTitle } : t))
    );
  };

  const handleDeleteTest = async (testId: number) => {
    if (!confirm('Are you sure you want to delete this test?')) {
      return;
    }

    try {
      await testsService.deleteTest(testId.toString());
      setTests(tests.filter((t) => t.id !== testId));
      alert('Test deleted successfully!');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete test');
    }
  };

  const toggleRowSelection = (id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleSelectAll = () => {
    if (selectedIds.size === filteredTests.length && filteredTests.length > 0) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredTests.map((t) => t.id)));
    }
  };

  const handleBatchDeleteConfirm = async () => {
    setBatchDeleting(true);
    try {
      const result = await testsService.batchDeleteTests([...selectedIds]);
      if (result.failed.length > 0) {
        alert(`${result.deleted} test(s) deleted. ${result.failed.length} could not be deleted.`);
      }
      setShowConfirmModal(false);
      setSelectedIds(new Set());
      await loadTests();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete tests');
    } finally {
      setBatchDeleting(false);
    }
  };

  const handleRunTest = async (testId: number) => {
    try {
      const execution = await executionService.startExecution(testId, {
        browser: 'chromium',
        environment: 'dev',
        base_url: 'https://web.three.com.hk',
      });
      navigate(`/executions/${execution.id}`);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to run test');
    }
  };

  const openScheduleModal = async (test: SavedTest) => {
    setScheduleTarget({ id: test.id, title: test.title });
    setLoadingSchedules(true);
    setExistingSchedules([]);
    try {
      const list = await schedulesService.listForTest(test.id);
      setExistingSchedules(list);
    } catch {
      // non-fatal
    } finally {
      setLoadingSchedules(false);
    }
  };

  const closeScheduleModal = () => {
    setScheduleTarget(null);
    setExistingSchedules([]);
  };

  const handleSaveSchedule = async () => {
    if (!scheduleTarget) return;
    setSavingSchedule(true);
    try {
      const payload: CreateSchedulePayload = {
        test_case_id: scheduleTarget.id,
        schedule_type: scheduleType,
        interval_minutes: scheduleType === 'interval' ? parseInt(intervalMinutes, 10) : undefined,
        cron_expression: scheduleType === 'cron' ? cronExpression : undefined,
        browser: scheduleBrowser,
        environment: scheduleEnvironment,
      };
      const created = await schedulesService.create(payload);
      setExistingSchedules((prev) => [...prev, created]);
      if (created.enabled) {
        setScheduledTestIds((prev) => ({
          ...prev,
          [created.test_case_id]: (prev[created.test_case_id] ?? 0) + 1,
        }));
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to create schedule');
    } finally {
      setSavingSchedule(false);
    }
  };

  const handleToggleSchedule = async (scheduleId: number) => {
    setTogglingScheduleId(scheduleId);
    try {
      const updated = await schedulesService.toggle(scheduleId);
      setExistingSchedules((prev) => prev.map((s) => (s.id === scheduleId ? updated : s)));
      setScheduledTestIds((prev) => {
        const newCounts = { ...prev };
        const delta = updated.enabled ? 1 : -1;
        newCounts[updated.test_case_id] = Math.max(0, (newCounts[updated.test_case_id] ?? 0) + delta);
        return newCounts;
      });
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to toggle schedule');
    } finally {
      setTogglingScheduleId(null);
    }
  };

  const handleDeleteSchedule = async (scheduleId: number) => {
    if (!confirm('Delete this schedule?')) return;
    try {
      const target = existingSchedules.find((s) => s.id === scheduleId);
      await schedulesService.remove(scheduleId);
      setExistingSchedules((prev) => prev.filter((s) => s.id !== scheduleId));
      if (target?.enabled && target.test_case_id) {
        setScheduledTestIds((prev) => ({
          ...prev,
          [target.test_case_id]: Math.max(0, (prev[target.test_case_id] ?? 1) - 1),
        }));
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete schedule');
    }
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

  const getTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'e2e':
        return 'bg-blue-100 text-blue-700';
      case 'integration':
        return 'bg-purple-100 text-purple-700';
      case 'unit':
        return 'bg-green-100 text-green-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const filteredTests = tests.filter((test) => {
    const matchesSearch =
      test.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      test.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'all' || test.test_type === filterType;
    const matchesPriority = filterPriority === 'all' || test.priority === filterPriority;
    const hasSchedule = (scheduledTestIds[test.id] ?? 0) > 0;
    const matchesScheduled =
      filterScheduled === 'all' ||
      (filterScheduled === 'scheduled' && hasSchedule) ||
      (filterScheduled === 'unscheduled' && !hasSchedule);
    return matchesSearch && matchesType && matchesPriority && matchesScheduled;
  });

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Saved Tests</h1>
            <p className="text-gray-600 mt-1">Manage and execute your saved test cases</p>
          </div>
          <Button variant="primary" onClick={() => navigate('/tests')}>
            <Plus className="w-5 h-5 mr-2" />
            Generate New Tests
          </Button>
        </div>

        <Card>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="md:col-span-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search Tests
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Search by title or description..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Test Type
              </label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Types</option>
                <option value="e2e">E2E</option>
                <option value="integration">Integration</option>
                <option value="unit">Unit</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Priority
              </label>
              <select
                value={filterPriority}
                onChange={(e) => setFilterPriority(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Priorities</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Schedule
              </label>
              <select
                value={filterScheduled}
                onChange={(e) => setFilterScheduled(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="all">All Tests</option>
                <option value="scheduled">Scheduled only</option>
                <option value="unscheduled">Not scheduled</option>
              </select>
            </div>
          </div>
        </Card>

        {!error && tests.length > 0 && (
          <div className="flex items-center gap-4 py-2">
            <label className="flex items-center gap-2 cursor-pointer text-sm text-gray-600">
              <input
                type="checkbox"
                data-testid="select-all-checkbox"
                checked={filteredTests.length > 0 && selectedIds.size === filteredTests.length}
                onChange={handleSelectAll}
                className="w-4 h-4"
              />
              Select All
            </label>
            <Button
              variant="danger"
              disabled={selectedIds.size === 0 || batchDeleting}
              onClick={() => setShowConfirmModal(true)}
              data-testid="batch-delete-button"
            >
              <Trash2 className="w-4 h-4 mr-1" />
              Delete Selected ({selectedIds.size})
            </Button>
          </div>
        )}

        {error && (
          <Card>
            <div className="text-center py-8">
              <p className="text-red-600 mb-4">{error}</p>
              <Button variant="primary" onClick={loadTests}>
                Retry
              </Button>
            </div>
          </Card>
        )}

        {!error && filteredTests.length === 0 && (
          <Card>
            <div className="text-center py-12">
              <p className="text-gray-600 mb-4">
                {tests.length === 0
                  ? 'No saved tests yet. Generate some tests to get started!'
                  : 'No tests match your filters.'}
              </p>
              {tests.length === 0 && (
                <Button variant="primary" onClick={() => navigate('/tests')}>
                  <Plus className="w-5 h-5 mr-2" />
                  Generate Tests
                </Button>
              )}
            </div>
          </Card>
        )}

        {!error && filteredTests.length > 0 && (
          <div className="grid gap-4">
            {filteredTests.map((test) => (
              <Card key={test.id}>
                <div className="flex justify-between items-start">
                  <div className="flex items-start pt-1 pr-3">
                    <input
                      type="checkbox"
                      data-testid={`row-checkbox-${test.id}`}
                      checked={selectedIds.has(test.id)}
                      onChange={() => toggleRowSelection(test.id)}
                      disabled={batchDeleting}
                      className="w-4 h-4 cursor-pointer"
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start gap-3 mb-2 flex-wrap">
                      <InlineTitleEditor
                        testId={test.id}
                        title={test.title}
                        onTitleChange={(newTitle) => handleTitleChange(test.id, newTitle)}
                        disabled={batchDeleting}
                      />
                      {scheduledTestIds[test.id] > 0 && (
                        <span
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-700 cursor-pointer hover:bg-indigo-200"
                          title={`${scheduledTestIds[test.id]} active schedule${scheduledTestIds[test.id] !== 1 ? 's' : ''} — click clock icon to manage`}
                        >
                          <Clock className="w-3 h-3" />
                          {scheduledTestIds[test.id]}
                        </span>
                      )}
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(
                          test.priority
                        )}`}
                      >
                        {test.priority}
                      </span>
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${getTypeColor(
                          test.test_type
                        )}`}
                      >
                        {test.test_type}
                      </span>
                    </div>
                    <p className="text-gray-600 mb-3">{test.description}</p>
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span>ID: #{test.id}</span>
                      <span>Created: {new Date(test.created_at).toLocaleDateString()}</span>
                      <span>Updated: {new Date(test.updated_at).toLocaleDateString()}</span>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() => navigate(`/tests/${test.id}`)}
                      className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      title="View Details"
                    >
                      <Eye className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => navigate(`/tests/saved?edit=${test.id}`)}
                      className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                      title="Edit Test"
                    >
                      <Edit className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => handleRunTest(test.id)}
                      className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                      title="Run Test"
                    >
                      <Play className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => openScheduleModal(test)}
                      className="p-2 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                      title="Schedule Test"
                    >
                      <Clock className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => handleDeleteTest(test.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete Test"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}

        {!error && tests.length > 0 && (
          <div className="text-sm text-gray-600 text-center">
            Showing {filteredTests.length} of {tests.length} test{tests.length !== 1 ? 's' : ''}
          </div>
        )}
      </div>

      {(editingTest || editLoading) && (
        <div className="fixed inset-0 z-50 flex">
          <div
            className="flex-1 bg-black bg-opacity-50"
            onClick={closeEditDrawer}
            aria-hidden="true"
          />
          <div className="w-full max-w-2xl bg-white shadow-xl overflow-y-auto flex flex-col">
            <div className="p-6 space-y-4 flex-1">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-gray-900">Edit Test Case</h2>
                <button
                  onClick={closeEditDrawer}
                  className="text-gray-500 hover:text-gray-700 text-xl"
                  aria-label="Close edit drawer"
                >
                  ✕
                </button>
              </div>

              {editLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                </div>
              ) : (
                <div className="space-y-4">
                  <div>
                    <label htmlFor="saved-edit-title" className="block text-sm font-semibold text-gray-900 mb-2">
                      Title
                    </label>
                    <input
                      id="saved-edit-title"
                      type="text"
                      value={editForm.title}
                      onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                      className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-700 focus:border-blue-700 bg-white"
                    />
                  </div>

                  <div>
                    <label htmlFor="saved-edit-description" className="block text-sm font-semibold text-gray-900 mb-2">
                      Description
                    </label>
                    <textarea
                      id="saved-edit-description"
                      value={editForm.description}
                      onChange={(e) =>
                        setEditForm({ ...editForm, description: e.target.value })
                      }
                      className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-700 focus:border-blue-700 min-h-[80px] bg-white"
                    />
                  </div>

                  <div>
                    <label htmlFor="saved-edit-priority" className="block text-sm font-semibold text-gray-900 mb-2">
                      Priority
                    </label>
                    <select
                      id="saved-edit-priority"
                      value={editForm.priority}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          priority: e.target.value as 'high' | 'medium' | 'low',
                        })
                      }
                      className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-700 focus:border-blue-700 bg-white"
                    >
                      <option value="high">High</option>
                      <option value="medium">Medium</option>
                      <option value="low">Low</option>
                    </select>
                  </div>

                  <div className="flex items-center justify-between p-3 border-2 border-amber-200 rounded-lg bg-amber-50">
                    <div>
                      <label
                        htmlFor="saved-edit-requires-creds"
                        className="block text-sm font-semibold text-gray-900"
                      >
                        🔐 Requires CRM Login
                      </label>
                      <p className="text-xs text-gray-500 mt-0.5">
                        Show credential prompt before each run (never stored)
                      </p>
                    </div>
                    <input
                      id="saved-edit-requires-creds"
                      type="checkbox"
                      checked={editForm.requires_runtime_credentials}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          requires_runtime_credentials: e.target.checked,
                        })
                      }
                      className="w-5 h-5 accent-amber-500 cursor-pointer"
                      data-testid="requires-runtime-credentials-toggle"
                    />
                  </div>

                  {editingTest && (
                    <TestStepEditor
                      testId={Number(editingTest.id)}
                      initialSteps={editForm.steps.join('\n')}
                      initialVersion={
                        (editingTest as GeneratedTestCase & { current_version?: number }).current_version || 1
                      }
                      onSave={(versionNumber) => {
                        console.log('Version saved:', versionNumber);
                      }}
                    />
                  )}

                  <div>
                    <label htmlFor="saved-edit-expected-result" className="block text-sm font-semibold text-gray-900 mb-2">
                      Expected Result
                    </label>
                    <textarea
                      id="saved-edit-expected-result"
                      value={editForm.expected_result}
                      onChange={(e) =>
                        setEditForm({ ...editForm, expected_result: e.target.value })
                      }
                      className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-700 focus:border-blue-700 min-h-[80px] bg-white"
                    />
                  </div>

                  {editError && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
                      {editError}
                    </div>
                  )}
                </div>
              )}
            </div>

            {!editLoading && editingTest && (
              <div className="border-t p-6 flex gap-3">
                <Button
                  variant="secondary"
                  onClick={closeEditDrawer}
                  disabled={editSaving}
                >
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  onClick={handleSaveEdit}
                  disabled={editSaving}
                  className="flex-1"
                >
                  {editSaving ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    'Save Changes'
                  )}
                </Button>
              </div>
            )}
          </div>
        </div>
      )}

      {scheduleTarget && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 max-w-lg w-full mx-4 space-y-5 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <Clock className="w-5 h-5 text-indigo-600" />
                Schedule Test
              </h2>
              <button onClick={closeScheduleModal} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
            </div>
            <p className="text-sm text-gray-500 truncate">{scheduleTarget.title}</p>

            {loadingSchedules ? (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Loader2 className="w-4 h-4 animate-spin" /> Loading schedules…
              </div>
            ) : existingSchedules.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Active Schedules</p>
                {existingSchedules.map((s) => (
                  <div key={s.id} className="flex items-center justify-between rounded-lg border border-gray-200 px-3 py-2 text-sm">
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-gray-800 truncate">{s.schedule_description}</p>
                      <p className="text-xs text-gray-400">{s.browser} · {s.environment}{s.last_triggered_at ? ` · last run ${new Date(s.last_triggered_at).toLocaleString()}` : ''}</p>
                    </div>
                    <div className="flex items-center gap-2 ml-3">
                      <button
                        onClick={() => handleToggleSchedule(s.id)}
                        disabled={togglingScheduleId === s.id}
                        className={`text-xs px-2 py-1 rounded border transition-colors ${s.enabled ? 'border-green-300 text-green-700 hover:bg-green-50' : 'border-gray-300 text-gray-500 hover:bg-gray-50'}`}
                      >
                        {togglingScheduleId === s.id ? '…' : s.enabled ? 'On' : 'Off'}
                      </button>
                      <button
                        onClick={() => handleDeleteSchedule(s.id)}
                        className="text-xs px-2 py-1 rounded border border-red-200 text-red-600 hover:bg-red-50 transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="border-t pt-4 space-y-4">
              <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Add New Schedule</p>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Schedule Type</label>
                <select
                  value={scheduleType}
                  onChange={(e) => setScheduleType(e.target.value as 'interval' | 'cron')}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="interval">Interval (every N minutes)</option>
                  <option value="cron">Cron expression</option>
                </select>
              </div>

              {scheduleType === 'interval' ? (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Every (minutes)</label>
                  <input
                    type="number"
                    min={1}
                    value={intervalMinutes}
                    onChange={(e) => setIntervalMinutes(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="60"
                  />
                  <p className="text-xs text-gray-400 mt-1">e.g. 30 = every 30 minutes · 1440 = daily</p>
                </div>
              ) : (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Cron Expression</label>
                  <input
                    type="text"
                    value={cronExpression}
                    onChange={(e) => setCronExpression(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="0 9 * * *"
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    Standard 5-field cron: min hour dom mon dow · e.g. <code>0 9 * * 1-5</code> = weekdays 9am
                  </p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Browser</label>
                  <select
                    value={scheduleBrowser}
                    onChange={(e) => setScheduleBrowser(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="chromium">Chromium</option>
                    <option value="firefox">Firefox</option>
                    <option value="webkit">WebKit</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Environment</label>
                  <select
                    value={scheduleEnvironment}
                    onChange={(e) => setScheduleEnvironment(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="dev">Dev</option>
                    <option value="staging">Staging</option>
                    <option value="production">Production</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-1">
                <button
                  onClick={closeScheduleModal}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
                >
                  Close
                </button>
                <button
                  onClick={handleSaveSchedule}
                  disabled={savingSchedule}
                  className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {savingSchedule && <Loader2 className="w-4 h-4 animate-spin" />}
                  Add Schedule
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showConfirmModal && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          data-testid="batch-delete-modal"
        >
          <div className="bg-white rounded-xl shadow-xl p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold text-gray-900 mb-3">Delete Tests</h2>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete {selectedIds.size} test
              {selectedIds.size !== 1 ? 's' : ''}? This cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button
                data-testid="cancel-delete-button"
                onClick={() => setShowConfirmModal(false)}
                disabled={batchDeleting}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                data-testid="confirm-delete-button"
                onClick={handleBatchDeleteConfirm}
                disabled={batchDeleting}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
              >
                {batchDeleting && <Loader2 className="w-4 h-4 animate-spin" />}
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
};
