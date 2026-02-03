import React from 'react';
import { GeneratedTestCase } from '../../types/api';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { RunTestButton } from '../RunTestButton';
import { Check, Edit, Trash2 } from 'lucide-react';

interface TestCaseCardProps {
  testCase: GeneratedTestCase;
  onEdit?: (testCase: GeneratedTestCase) => void;
  onDelete?: (testCase: GeneratedTestCase) => void;
  onSave?: (testCase: GeneratedTestCase) => void;
  onExecutionStart?: (executionId: number) => void;
}

export const TestCaseCard: React.FC<TestCaseCardProps> = ({
  testCase,
  onEdit,
  onDelete,
  onSave,
  onExecutionStart,
}) => {
  const priorityColors = {
    high: 'bg-red-100 text-red-700',
    medium: 'bg-yellow-100 text-yellow-700',
    low: 'bg-blue-100 text-blue-700',
  };

  return (
    <Card padding={false}>
      <div className="p-4 space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-gray-900">{testCase.title}</h3>
              <span className={`text-xs px-2 py-1 rounded capitalize ${priorityColors[testCase.priority]}`}>
                {testCase.priority}
              </span>
            </div>
            {testCase.id && (
              <p className="text-xs text-gray-500 mt-1">{testCase.id}</p>
            )}
          </div>
          <div className="flex gap-2">
            {onExecutionStart && testCase.id && (
              <RunTestButton
                testCaseId={parseInt(testCase.id.replace(/\D/g, '')) || 1}
                onExecutionStart={onExecutionStart}
                enableProfileUpload
              />
            )}
            {onEdit && (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => onEdit(testCase)}
                title="Edit"
              >
                <Edit className="w-4 h-4 mr-1" />
                Edit
              </Button>
            )}
            {onDelete && (
              <Button
                variant="danger"
                size="sm"
                onClick={() => onDelete(testCase)}
                title="Delete"
              >
                <Trash2 className="w-4 h-4 mr-1" />
                Delete
              </Button>
            )}
            {onSave && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => onSave(testCase)}
                title="Save"
              >
                Save
              </Button>
            )}
          </div>
        </div>

        {/* Description */}
        <div>
          <p className="text-sm text-gray-700">{testCase.description}</p>
        </div>

        {/* Test Steps */}
        <div>
          <h4 className="text-sm font-semibold text-gray-900 mb-2">Test Steps:</h4>
          <ol className="space-y-2">
            {testCase.steps.map((step, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-700 text-white rounded-full flex items-center justify-center text-xs font-semibold">
                  {index + 1}
                </span>
                <span className="flex-1 pt-0.5">{step}</span>
              </li>
            ))}
          </ol>
        </div>

        {/* Expected Result */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
          <div className="flex items-start gap-2">
            <Check className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-semibold text-green-900 mb-1">Expected Result:</h4>
              <p className="text-sm text-green-800">{testCase.expected_result}</p>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};
