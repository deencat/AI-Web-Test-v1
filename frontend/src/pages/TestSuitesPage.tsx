import React, { useState, useEffect } from 'react';
import { Layout } from '../components/layout/Layout';
import testSuitesService, { TestSuite } from '../services/testSuitesService';
import CreateSuiteModal from '../components/CreateSuiteModal';

const TestSuitesPage: React.FC = () => {
  const [suites, setSuites] = useState<TestSuite[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [expandedSuites, setExpandedSuites] = useState<Set<number>>(new Set());

  useEffect(() => {
    loadSuites();
  }, []);

  const loadSuites = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await testSuitesService.getAllSuites();
      setSuites(data);
    } catch (err: any) {
      console.error('Failed to load test suites:', err);
      setError(err.response?.data?.detail || 'Failed to load test suites');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (suiteId: number, suiteName: string) => {
    if (!confirm(`Are you sure you want to delete the test suite "${suiteName}"?`)) {
      return;
    }

    try {
      await testSuitesService.deleteSuite(suiteId);
      setSuites(prev => prev.filter(s => s.id !== suiteId));
    } catch (err: any) {
      console.error('Failed to delete suite:', err);
      alert(err.response?.data?.detail || 'Failed to delete test suite');
    }
  };

  const handleRunSuite = async (suiteId: number, suiteName: string) => {
    const browser = prompt('Enter browser (chromium/firefox/webkit):', 'chromium');
    if (!browser) return;

    const environment = prompt('Enter environment (dev/staging/prod):', 'dev');
    if (!environment) return;

    const stopOnFailure = confirm('Stop execution if a test fails?');

    try {
      const result = await testSuitesService.runSuite(suiteId, {
        browser,
        environment,
        stop_on_failure: stopOnFailure,
        parallel: false
      });

      alert(`✅ ${result.message}\n\nSuite Execution ID: ${result.suite_execution_id}\nQueued Tests: ${result.queued_executions.length}`);
      
      // Navigate to executions page
      window.location.href = '/executions';
    } catch (err: any) {
      console.error('Failed to run suite:', err);
      alert(err.response?.data?.detail || 'Failed to run test suite');
    }
  };

  const toggleExpanded = (suiteId: number) => {
    setExpandedSuites(prev => {
      const newSet = new Set(prev);
      if (newSet.has(suiteId)) {
        newSet.delete(suiteId);
      } else {
        newSet.add(suiteId);
      }
      return newSet;
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <Layout>
        <div className="p-8">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading test suites...</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">Test Suites</h1>
            <p className="text-gray-600 mt-2">Group and run multiple tests together</p>
          </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Suite
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* Empty State */}
      {suites.length === 0 ? (
        <div className="text-center py-16 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
          <h3 className="text-xl font-semibold text-gray-800 mb-2">No Test Suites Yet</h3>
          <p className="text-gray-600 mb-4">Create your first test suite to group and run multiple tests together</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Create Your First Suite
          </button>
        </div>
      ) : (
        /* Suite Cards */
        <div className="space-y-4">
          {suites.map(suite => {
            const isExpanded = expandedSuites.has(suite.id);
            return (
              <div key={suite.id} className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow">
                {/* Suite Header */}
                <div className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-xl font-semibold text-gray-800">
                          📦 {suite.name}
                        </h3>
                        <button
                          onClick={() => toggleExpanded(suite.id)}
                          className="text-gray-500 hover:text-gray-700"
                        >
                          <svg
                            className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
                        <span>{suite.items?.length || 0} tests</span>
                        <span>•</span>
                        <span>Created {formatDate(suite.created_at)}</span>
                      </div>
                      {suite.description && (
                        <p className="text-gray-600 mb-3">{suite.description}</p>
                      )}
                      {suite.tags && suite.tags.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {suite.tags.map((tag, index) => (
                            <span
                              key={index}
                              className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="flex gap-2 ml-4">
                      <button
                        onClick={() => handleRunSuite(suite.id, suite.name)}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                        title="Run Suite"
                      >
                        Run
                      </button>
                      <button
                        onClick={() => handleDelete(suite.id, suite.name)}
                        className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                        title="Delete Suite"
                      >
                        Delete
                      </button>
                    </div>
                  </div>

                  {/* Expanded Test List */}
                  {isExpanded && suite.items && suite.items.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <h4 className="font-semibold text-gray-700 mb-3">Tests in this suite:</h4>
                      <div className="space-y-2">
                        {suite.items
                          .sort((a, b) => a.execution_order - b.execution_order)
                          .map(item => (
                            <div
                              key={item.id}
                              className="flex items-center gap-3 p-3 bg-gray-50 rounded border border-gray-200"
                            >
                              <span className="font-semibold text-gray-600 w-8">
                                {item.execution_order}.
                              </span>
                              <div className="flex-1">
                                <span className="text-gray-800">
                                  {item.test_case?.title || `Test #${item.test_case_id}`}
                                </span>
                                <span className="text-gray-500 text-sm ml-2">
                                  (#{item.test_case_id})
                                </span>
                              </div>
                              <span className="text-green-500">✅</span>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Suite Modal */}
      <CreateSuiteModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={loadSuites}
      />
      </div>
    </Layout>
  );
};

export default TestSuitesPage;
