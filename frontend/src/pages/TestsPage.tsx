import React, { useState, useEffect } from 'react';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { TestCaseCard } from '../components/tests/TestCaseCard';
import { RunTestButton } from '../components/RunTestButton';
import { TestStepEditor } from '../components/TestStepEditor';
import { mockTests } from '../mock/tests';
import testsService from '../services/testsService';
import knowledgeBaseService from '../services/knowledgeBaseService';
import { GeneratedTestCase, KBCategory } from '../types/api';
import { Sparkles, Loader2, BookOpen } from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';

export const TestsPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [filter, setFilter] = useState('all');
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [generatedTests, setGeneratedTests] = useState<GeneratedTestCase[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showGenerator, setShowGenerator] = useState(true);
  const [editingTest, setEditingTest] = useState<GeneratedTestCase | null>(null);
  const [editingSavedTest, setEditingSavedTest] = useState(false);
  const [editForm, setEditForm] = useState({
    title: '',
    description: '',
    steps: [] as string[],
    expected_result: '',
    priority: 'medium' as 'high' | 'medium' | 'low',
  });
  
  // KB Integration State (Sprint 2 Day 11)
  const [kbCategories, setKbCategories] = useState<KBCategory[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [useKBContext, setUseKBContext] = useState(true);
  const [loadingCategories, setLoadingCategories] = useState(false);

  // Handle edit parameter from URL
  useEffect(() => {
    const editId = searchParams.get('edit');
    if (editId) {
      loadAndEditTest(editId);
    }
  }, [searchParams]);
  
  // Load KB categories on mount (Sprint 2 Day 11)
  useEffect(() => {
    loadKBCategories();
  }, []);
  
  const loadKBCategories = async () => {
    try {
      setLoadingCategories(true);
      const categories = await knowledgeBaseService.getAllCategories();
      setKbCategories(categories);
    } catch (err) {
      console.error('Failed to load KB categories:', err);
      // Don't show error to user - KB categories are optional
    } finally {
      setLoadingCategories(false);
    }
  };

  const loadAndEditTest = async (testId: string) => {
    try {
      setLoading(true);
      setError(null);
      const test = await testsService.getTestById(testId);
      
      // Convert saved test to GeneratedTestCase format for editing
      // Backend returns: { id, title, description, steps, expected_result, priority, ... }
      const testCase: GeneratedTestCase = {
        id: test.id?.toString() || testId,
        title: (test as any).title || test.name || '',
        description: test.description || '',
        steps: Array.isArray((test as any).steps) 
          ? (test as any).steps.map((step: any) => typeof step === 'string' ? step : step.description || '')
          : [],
        expected_result: (test as any).expected_result || '',
        priority: test.priority as 'high' | 'medium' | 'low',
      };
      
      setEditingTest(testCase);
      setEditingSavedTest(true);
      setShowGenerator(false);
      setEditForm({
        title: testCase.title,
        description: testCase.description,
        steps: [...testCase.steps],
        expected_result: testCase.expected_result,
        priority: testCase.priority,
      });
    } catch (err) {
      console.error('Failed to load test:', err);
      setError(err instanceof Error ? err.message : 'Failed to load test');
      alert('Failed to load test for editing. Redirecting to saved tests page.');
      navigate('/tests/saved');
    } finally {
      setLoading(false);
    }
  };

  const handleExecutionStart = (executionId: number) => {
    navigate(`/executions/${executionId}`);
  };

  const handleGenerateTests = async () => {
    if (!prompt.trim()) {
      setError('Please enter a test description');
      return;
    }

    // Validate minimum length (backend requires 10 chars)
    if (prompt.trim().length < 10) {
      setError('Test requirement must be at least 10 characters long');
      return;
    }

    // Validate maximum length (backend allows max 2000 chars)
    if (prompt.trim().length > 2000) {
      setError('Test requirement cannot exceed 2000 characters');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await testsService.generateTests({ 
        requirement: prompt,
        num_tests: 5,
        // KB Integration (Sprint 2 Day 11)
        category_id: selectedCategory || undefined,
        use_kb_context: useKBContext,
        max_kb_docs: 10
      });
      setGeneratedTests(result.test_cases);
      setShowGenerator(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate tests');
    } finally {
      setLoading(false);
    }
  };

  const handleEditTest = (testCase: GeneratedTestCase) => {
    setEditingTest(testCase);
    setEditingSavedTest(false); // This is a generated test
    setEditForm({
      title: testCase.title,
      description: testCase.description,
      steps: [...testCase.steps],
      expected_result: testCase.expected_result,
      priority: testCase.priority,
    });
  };

  const handleSaveEdit = async () => {
    if (!editingTest) return;

    // If editing a saved test, update it in the database
    if (editingSavedTest) {
      try {
        setLoading(true);
        setError(null);
        
        await testsService.updateTest(editingTest.id!, {
          title: editForm.title,
          description: editForm.description,
          priority: editForm.priority,
          steps: editForm.steps,
          expected_result: editForm.expected_result,
        });
        
        alert(`✅ Test "${editForm.title}" updated successfully!`);
        navigate('/tests/saved');
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to update test';
        setError(errorMessage);
        alert(`❌ Error updating test: ${errorMessage}`);
      } finally {
        setLoading(false);
      }
    } else {
      // Editing a generated test (not yet saved)
      const updatedTests = generatedTests.map((test) =>
        test.id === editingTest.id
          ? { ...editingTest, ...editForm }
          : test
      );
      setGeneratedTests(updatedTests);
      setEditingTest(null);
      setEditingSavedTest(false);
    }
  };

  const handleCancelEdit = () => {
    if (editingSavedTest) {
      // If was editing a saved test, go back to saved tests page
      navigate('/tests/saved');
    }
    setEditingTest(null);
    setEditingSavedTest(false);
  };

  const handleSaveTest = async (testCase: GeneratedTestCase) => {
    try {
      setLoading(true);
      setError(null);
      
      // Create the test case using the API
      const createRequest: any = {
        title: testCase.title,
        description: testCase.description,
        test_type: 'e2e', // Default to e2e for generated tests
        priority: testCase.priority || 'medium',
        status: 'pending',
        steps: testCase.steps,
        expected_result: testCase.expected_result
      };
      
      await testsService.createTest(createRequest);
      
      // Remove from generated tests after saving
      setGeneratedTests(generatedTests.filter((t) => t.id !== testCase.id));
      
      alert(`✅ Test "${testCase.title}" saved successfully!`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save test';
      setError(errorMessage);
      alert(`❌ Error saving test: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveAllTests = async () => {
    if (generatedTests.length === 0) {
      alert('No tests to save');
      return;
    }
    
    if (!confirm(`Save all ${generatedTests.length} test cases?`)) {
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      let savedCount = 0;
      let failedCount = 0;
      
      for (const testCase of generatedTests) {
        try {
          const createRequest: any = {
            title: testCase.title,
            description: testCase.description,
            test_type: 'e2e', // Default to e2e for generated tests
            priority: testCase.priority || 'medium',
            status: 'pending',
            steps: testCase.steps,
            expected_result: testCase.expected_result
          };
          
          await testsService.createTest(createRequest);
          savedCount++;
        } catch (err) {
          console.error(`Failed to save test "${testCase.title}":`, err);
          failedCount++;
        }
      }
      
      // Clear all generated tests after saving
      setGeneratedTests([]);
      
      if (failedCount === 0) {
        alert(`✅ Successfully saved all ${savedCount} test cases!`);
      } else {
        alert(`⚠️ Saved ${savedCount} tests, but ${failedCount} failed to save.`);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save tests';
      setError(errorMessage);
      alert(`❌ Error: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTest = (testCase: GeneratedTestCase) => {
    if (confirm(`Delete test: ${testCase.title}?`)) {
      setGeneratedTests(generatedTests.filter((t) => t.id !== testCase.id));
    }
  };

  const handleCreateTest = () => {
    setShowGenerator(true);
    setGeneratedTests([]);
    setPrompt('');
    setError(null);
  };

  const handleViewDetails = (testId: string) => {
    alert(`View test details for ${testId}`);
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Test Cases</h1>
            <p className="text-gray-600 mt-1">
              {showGenerator
                ? 'Generate test cases using natural language'
                : 'Manage and execute your test cases'}
            </p>
          </div>
          <div className="flex gap-3">
            {!showGenerator && (
              <>
                <Button variant="secondary" onClick={() => navigate('/tests/saved')}>
                  View Saved Tests
                </Button>
                <Button variant="primary" onClick={handleCreateTest}>
                  <Sparkles className="w-5 h-5 mr-2" />
                  Generate New Tests
                </Button>
              </>
            )}
            {showGenerator && (
              <Button variant="secondary" onClick={() => navigate('/tests/saved')}>
                View Saved Tests
              </Button>
            )}
          </div>
        </div>

        {/* Test Generation Form */}
        {showGenerator && (
          <Card>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-900 mb-2">
                  Describe the test you want to create:
                  <span className="text-xs text-gray-500 ml-2 font-normal">
                    (minimum 10 characters)
                  </span>
                </label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Example: Test the login flow for Three HK website with valid credentials"
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-700 focus:border-blue-700 min-h-[120px] resize-y bg-white"
                  disabled={loading}
                />
                <p className="text-xs text-gray-500 mt-2">
                  Be specific about what you want to test. Include details like:
                  user actions, expected outcomes, and test data. Minimum 10 characters required.
                </p>
              </div>
              
              {/* KB Integration Options (Sprint 2 Day 11) */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-3">
                <div className="flex items-start gap-2">
                  <BookOpen className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <h3 className="text-sm font-semibold text-gray-900 mb-1">
                      Knowledge Base Context
                    </h3>
                    <p className="text-xs text-gray-600 mb-3">
                      Use uploaded KB documents to generate more accurate, domain-specific tests
                      with proper field names and workflows.
                    </p>
                    
                    {/* Use KB Context Toggle */}
                    <div className="flex items-center gap-2 mb-3">
                      <input
                        type="checkbox"
                        id="use-kb-context"
                        checked={useKBContext}
                        onChange={(e) => setUseKBContext(e.target.checked)}
                        disabled={loading}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      <label htmlFor="use-kb-context" className="text-sm text-gray-700 cursor-pointer">
                        Use Knowledge Base context (recommended)
                      </label>
                    </div>
                    
                    {/* Category Selection */}
                    {useKBContext && (
                      <div>
                        <label htmlFor="kb-category" className="block text-xs font-medium text-gray-700 mb-1">
                          KB Category (optional)
                        </label>
                        <select
                          id="kb-category"
                          value={selectedCategory || ''}
                          onChange={(e) => setSelectedCategory(e.target.value ? Number(e.target.value) : null)}
                          disabled={loading || loadingCategories}
                          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                        >
                          <option value="">No specific category (use all KB documents)</option>
                          {kbCategories.map((category) => (
                            <option key={category.id} value={category.id}>
                              {category.name} - {category.description}
                            </option>
                          ))}
                        </select>
                        <p className="text-xs text-gray-500 mt-1">
                          {selectedCategory 
                            ? 'Tests will reference specific KB documents from this category'
                            : 'Tests will use general knowledge without KB context'
                          }
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
                  {error}
                </div>
              )}

              <div className="flex gap-3">
                <Button
                  variant="primary"
                  onClick={handleGenerateTests}
                  disabled={loading || !prompt.trim()}
                  className="flex-1"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      Generating Tests...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5 mr-2" />
                      Generate Test Cases
                    </>
                  )}
                </Button>
              </div>
            </div>
          </Card>
        )}

        {/* Generated Tests Display */}
        {generatedTests.length > 0 && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-900">
                Generated Test Cases ({generatedTests.length})
              </h2>
              <p className="text-sm text-gray-600">
                Review and save the test cases you want to use
              </p>
            </div>

            <div className="grid gap-4">
              {generatedTests.map((testCase, index) => (
                <TestCaseCard
                  key={testCase.id || index}
                  testCase={testCase}
                  onSave={handleSaveTest}
                  onEdit={handleEditTest}
                  onDelete={handleDeleteTest}
                  onExecutionStart={handleExecutionStart}
                />
              ))}
            </div>

            <div className="flex gap-3">
              <Button variant="primary" onClick={handleSaveAllTests} disabled={loading}>
                {loading ? 'Saving...' : 'Save All Tests'}
              </Button>
              <Button variant="secondary" onClick={handleCreateTest}>
                Generate More Tests
              </Button>
            </div>
          </div>
        )}

        {/* Edit Modal */}
        {editingTest && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <Card className="max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h2 className="text-2xl font-bold text-gray-900">Edit Test Case</h2>
                  <button
                    onClick={handleCancelEdit}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    ✕
                  </button>
                </div>

                <div className="space-y-4">
                  {/* Title */}
                  <div>
                    <label htmlFor="edit-title" className="block text-sm font-semibold text-gray-900 mb-2">
                      Title
                    </label>
                    <input
                      id="edit-title"
                      type="text"
                      value={editForm.title}
                      onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                      className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-700 focus:border-blue-700 bg-white"
                    />
                  </div>

                  {/* Description */}
                  <div>
                    <label htmlFor="edit-description" className="block text-sm font-semibold text-gray-900 mb-2">
                      Description
                    </label>
                    <textarea
                      id="edit-description"
                      value={editForm.description}
                      onChange={(e) =>
                        setEditForm({ ...editForm, description: e.target.value })
                      }
                      className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-700 focus:border-blue-700 min-h-[80px] bg-white"
                    />
                  </div>

                  {/* Priority */}
                  <div>
                    <label htmlFor="edit-priority" className="block text-sm font-semibold text-gray-900 mb-2">
                      Priority
                    </label>
                    <select
                      id="edit-priority"
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

                  {/* Test Steps - Version Control Enabled */}
                  {editingTest && (
                    <TestStepEditor
                      testId={Number(editingTest.id)}
                      initialSteps={editForm.steps}
                      initialVersion={(editingTest as any).current_version || 1}
                      onChange={(newSteps) => {
                        setEditForm({ ...editForm, steps: newSteps });
                      }}
                      onSave={(versionNumber, steps) => {
                        console.log('Version saved:', versionNumber);
                        setEditForm({ ...editForm, steps });
                      }}
                    />
                  )}

                  {/* Expected Result */}
                  <div>
                    <label htmlFor="edit-expected-result" className="block text-sm font-semibold text-gray-900 mb-2">
                      Expected Result
                    </label>
                    <textarea
                      id="edit-expected-result"
                      value={editForm.expected_result}
                      onChange={(e) =>
                        setEditForm({ ...editForm, expected_result: e.target.value })
                      }
                      className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-700 focus:border-blue-700 min-h-[80px] bg-white"
                    />
                  </div>
                </div>

                <div className="flex gap-3">
                  <Button variant="primary" onClick={handleSaveEdit} className="flex-1">
                    Save Changes
                  </Button>
                  <Button variant="secondary" onClick={handleCancelEdit}>
                    Cancel
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* Existing Tests Section */}
        {!showGenerator && generatedTests.length === 0 && (
          <>
            {/* Filter Buttons */}
            <div className="flex gap-2">
              <Button
                variant={filter === 'all' ? 'primary' : 'secondary'}
                onClick={() => setFilter('all')}
              >
                All
              </Button>
              <Button
                variant={filter === 'passed' ? 'primary' : 'secondary'}
                onClick={() => setFilter('passed')}
              >
                Passed
              </Button>
              <Button
                variant={filter === 'failed' ? 'primary' : 'secondary'}
                onClick={() => setFilter('failed')}
              >
                Failed
              </Button>
              <Button
                variant={filter === 'pending' ? 'primary' : 'secondary'}
                onClick={() => setFilter('pending')}
              >
                Pending
              </Button>
            </div>

            <Card>
              <div className="space-y-4">
                {mockTests.map((test) => (
                  <div
                    key={test.id}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex items-center gap-4 flex-1">
                      <div
                        className={`w-4 h-4 rounded-full flex-shrink-0 ${
                          test.status === 'passed'
                            ? 'bg-success'
                            : test.status === 'failed'
                            ? 'bg-danger'
                            : 'bg-warning animate-pulse'
                        }`}
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <p className="font-semibold text-gray-900">{test.name}</p>
                          <span className="text-xs px-2 py-1 bg-gray-200 text-gray-700 rounded">
                            {test.id}
                          </span>
                          <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded capitalize">
                            {test.priority}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">{test.description}</p>
                        <p className="text-xs text-gray-500 mt-1">Agent: {test.agent}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <p
                          className={`text-sm font-medium ${
                            test.status === 'passed'
                              ? 'text-success'
                              : test.status === 'failed'
                              ? 'text-danger'
                              : 'text-warning'
                          }`}
                        >
                          {test.status}
                        </p>
                        <p className="text-xs text-gray-500">
                          {test.status === 'running'
                            ? 'In Progress'
                            : `${test.execution_time}s`}
                        </p>
                      </div>
                      <RunTestButton
                        testCaseId={parseInt(test.id.replace('test-', ''))}
                        onExecutionStart={handleExecutionStart}
                        enableProfileUpload
                      />
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleViewDetails(test.id)}
                      >
                        View Details
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </>
        )}
      </div>
    </Layout>
  );
};

