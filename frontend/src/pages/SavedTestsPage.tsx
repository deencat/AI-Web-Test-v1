import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import testsService from '../services/testsService';
import executionService from '../services/executionService';
import { Loader2, Plus, Search, Trash2, Play, Eye, Edit } from 'lucide-react';

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
  const [tests, setTests] = useState<SavedTest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterPriority, setFilterPriority] = useState('all');

  useEffect(() => {
    loadTests();
  }, []);

  const loadTests = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await testsService.getAllTests();
      // getAllTests returns Test[], so we can use it directly
      setTests(response as any);
    } catch (err) {
      console.error('Failed to load tests:', err);
      setError(err instanceof Error ? err.message : 'Failed to load tests');
    } finally {
      setLoading(false);
    }
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

  const handleRunTest = async (testId: number) => {
    try {
      // Note: base_url will be extracted from test case steps automatically
      // For tests with explicit URLs in steps, this can be a placeholder
      const execution = await executionService.startExecution(testId, {
        browser: 'chromium',
        environment: 'dev',
        base_url: 'https://web.three.com.hk', // Base domain (actual URL comes from test steps)
      });
      navigate(`/executions/${execution.id}`);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to run test');
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

  // Filter tests
  const filteredTests = tests.filter((test) => {
    const matchesSearch =
      test.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      test.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'all' || test.test_type === filterType;
    const matchesPriority = filterPriority === 'all' || test.priority === filterPriority;
    return matchesSearch && matchesType && matchesPriority;
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
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Saved Test Cases</h1>
            <p className="text-gray-600 mt-1">Manage and execute your saved test cases</p>
          </div>
          <Button variant="primary" onClick={() => navigate('/tests')}>
            <Plus className="w-5 h-5 mr-2" />
            Generate New Tests
          </Button>
        </div>

        {/* Filters */}
        <Card>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
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

            {/* Type Filter */}
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

            {/* Priority Filter */}
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
          </div>
        </Card>

        {/* Error Display */}
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

        {/* Tests List */}
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
                  <div className="flex-1">
                    <div className="flex items-start gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">{test.title}</h3>
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
                      onClick={() => navigate(`/tests?edit=${test.id}`)}
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

        {/* Summary */}
        {!error && tests.length > 0 && (
          <div className="text-sm text-gray-600 text-center">
            Showing {filteredTests.length} of {tests.length} test{tests.length !== 1 ? 's' : ''}
          </div>
        )}
      </div>
    </Layout>
  );
};
