import React, { useState } from 'react';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { mockTests } from '../mock/tests';

export const TestsPage: React.FC = () => {
  const [filter, setFilter] = useState('all');

  const handleCreateTest = () => {
    alert('Create New Test - This will open a modal to create a new test');
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
            <p className="text-gray-600 mt-1">Manage and execute your test cases</p>
          </div>
          <Button variant="primary" onClick={handleCreateTest}>
            Create New Test
          </Button>
        </div>

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
                  <div className={`w-4 h-4 rounded-full flex-shrink-0 ${
                    test.status === 'passed' ? 'bg-success' :
                    test.status === 'failed' ? 'bg-danger' :
                    'bg-warning animate-pulse'
                  }`} />
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
                    <p className={`text-sm font-medium ${
                      test.status === 'passed' ? 'text-success' :
                      test.status === 'failed' ? 'text-danger' :
                      'text-warning'
                    }`}>
                      {test.status}
                    </p>
                    <p className="text-xs text-gray-500">
                      {test.status === 'running' ? 'In Progress' : `${test.execution_time}s`}
                    </p>
                  </div>
                  <Button variant="secondary" size="sm" onClick={() => handleViewDetails(test.id)}>
                    View Details
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </Layout>
  );
};

