import React, { useState, useEffect } from 'react';
import testsService from '../services/testsService';
import testSuitesService, { CreateTestSuiteRequest } from '../services/testSuitesService';

interface CreateSuiteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

interface TestCase {
  id: number;
  title: string;
  description?: string;
}

const CreateSuiteModal: React.FC<CreateSuiteModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [tagsInput, setTagsInput] = useState('');
  const [availableTests, setAvailableTests] = useState<TestCase[]>([]);
  const [selectedTestIds, setSelectedTestIds] = useState<number[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadAvailableTests();
    }
  }, [isOpen]);

  const loadAvailableTests = async () => {
    try {
      const response = await testsService.getAllTests();
      const tests = Array.isArray(response) ? response : (response as any).items || [];
      setAvailableTests(tests);
    } catch (err) {
      console.error('Failed to load tests:', err);
      setError('Failed to load available tests');
    }
  };

  const handleToggleTest = (testId: number) => {
    setSelectedTestIds(prev => 
      prev.includes(testId) 
        ? prev.filter(id => id !== testId)
        : [...prev, testId]
    );
  };

  const handleMoveUp = (index: number) => {
    if (index > 0) {
      const newOrder = [...selectedTestIds];
      [newOrder[index - 1], newOrder[index]] = [newOrder[index], newOrder[index - 1]];
      setSelectedTestIds(newOrder);
    }
  };

  const handleMoveDown = (index: number) => {
    if (index < selectedTestIds.length - 1) {
      const newOrder = [...selectedTestIds];
      [newOrder[index], newOrder[index + 1]] = [newOrder[index + 1], newOrder[index]];
      setSelectedTestIds(newOrder);
    }
  };

  const handleRemoveTest = (testId: number) => {
    setSelectedTestIds(prev => prev.filter(id => id !== testId));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name.trim()) {
      setError('Suite name is required');
      return;
    }

    if (selectedTestIds.length === 0) {
      setError('Please select at least one test case');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const tags = tagsInput
        .split(',')
        .map(tag => tag.trim())
        .filter(tag => tag.length > 0);

      const data: CreateTestSuiteRequest = {
        name: name.trim(),
        description: description.trim() || undefined,
        tags: tags.length > 0 ? tags : undefined,
        test_case_ids: selectedTestIds
      };

      await testSuitesService.createSuite(data);
      onSuccess();
      handleClose();
    } catch (err: any) {
      console.error('Failed to create suite:', err);
      setError(err.response?.data?.detail || 'Failed to create test suite');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setName('');
    setDescription('');
    setTagsInput('');
    setSelectedTestIds([]);
    setSearchQuery('');
    setError('');
    onClose();
  };

  const filteredTests = availableTests.filter(test =>
    test.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    test.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getTestById = (id: number) => availableTests.find(t => t.id === id);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-800">Create Test Suite</h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="overflow-y-auto max-h-[calc(90vh-140px)]">
          <div className="p-6 space-y-6">
            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            {/* Suite Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Suite Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., Three.com.hk Complete Flow"
                required
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Full subscription flow from plan selection to confirmation"
                rows={3}
              />
            </div>

            {/* Tags */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tags (comma-separated)
              </label>
              <input
                type="text"
                value={tagsInput}
                onChange={(e) => setTagsInput(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e2e, critical, three-hk"
              />
            </div>

            {/* Test Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Test Cases <span className="text-red-500">*</span>
              </label>
              
              {/* Search */}
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent mb-4"
                placeholder="Search tests... 🔍"
              />

              <div className="grid grid-cols-2 gap-4">
                {/* Available Tests */}
                <div>
                  <h3 className="font-medium text-gray-700 mb-2">Available Tests</h3>
                  <div className="border border-gray-300 rounded-lg p-4 h-64 overflow-y-auto bg-gray-50">
                    {filteredTests.length === 0 ? (
                      <p className="text-gray-500 text-center py-8">No tests available</p>
                    ) : (
                      <div className="space-y-2">
                        {filteredTests.map(test => (
                          <label
                            key={test.id}
                            className={`flex items-start p-2 rounded cursor-pointer hover:bg-gray-100 ${
                              selectedTestIds.includes(test.id) ? 'bg-blue-50' : ''
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={selectedTestIds.includes(test.id)}
                              onChange={() => handleToggleTest(test.id)}
                              className="mt-1 mr-3"
                            />
                            <div className="flex-1">
                              <div className="font-medium text-sm">#{test.id} {test.title}</div>
                              {test.description && (
                                <div className="text-xs text-gray-500 mt-1">{test.description}</div>
                              )}
                            </div>
                          </label>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Selected Tests (Ordered) */}
                <div>
                  <h3 className="font-medium text-gray-700 mb-2">
                    Selected Tests ({selectedTestIds.length}) - Drag to reorder
                  </h3>
                  <div className="border border-gray-300 rounded-lg p-4 h-64 overflow-y-auto bg-gray-50">
                    {selectedTestIds.length === 0 ? (
                      <p className="text-gray-500 text-center py-8">No tests selected</p>
                    ) : (
                      <div className="space-y-2">
                        {selectedTestIds.map((testId, index) => {
                          const test = getTestById(testId);
                          if (!test) return null;
                          return (
                            <div
                              key={testId}
                              className="flex items-center gap-2 p-2 bg-white border border-gray-200 rounded"
                            >
                              <span className="text-sm font-semibold text-gray-600 w-6">
                                {index + 1}.
                              </span>
                              <div className="flex-1 text-sm">
                                #{test.id} {test.title}
                              </div>
                              <div className="flex gap-1">
                                <button
                                  type="button"
                                  onClick={() => handleMoveUp(index)}
                                  disabled={index === 0}
                                  className="p-1 text-gray-500 hover:text-gray-700 disabled:opacity-30"
                                  title="Move up"
                                >
                                  ↑
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleMoveDown(index)}
                                  disabled={index === selectedTestIds.length - 1}
                                  className="p-1 text-gray-500 hover:text-gray-700 disabled:opacity-30"
                                  title="Move down"
                                >
                                  ↓
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleRemoveTest(testId)}
                                  className="p-1 text-red-500 hover:text-red-700"
                                  title="Remove"
                                >
                                  ×
                                </button>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 px-6 py-4 bg-gray-50 border-t">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={loading || selectedTestIds.length === 0}
            >
              {loading ? 'Creating...' : 'Create Suite'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateSuiteModal;
