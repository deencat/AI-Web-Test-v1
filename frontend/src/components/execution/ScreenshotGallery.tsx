import { useState } from 'react';
import { Card } from '../common/Card';
import { ScreenshotModal } from './ScreenshotModal';
import type { TestExecutionDetail } from '../../types/execution';
import executionService from '../../services/executionService';

interface ScreenshotGalleryProps {
  steps: TestExecutionDetail['steps'];
}

export function ScreenshotGallery({ steps }: ScreenshotGalleryProps) {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

  // Filter steps that have screenshots
  const screenshots = steps
    .filter((step) => step.screenshot_after)
    .map((step) => ({
      path: executionService.getScreenshotUrl(step.screenshot_after!),
      stepNumber: step.step_number,
      description: step.step_description,
      expectedResult: step.expected_result,
      actualResult: step.actual_result,
      status: step.result || 'pending',
    }));

  if (screenshots.length === 0) {
    return (
      <Card className="p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Screenshots</h2>
        <div className="text-center py-8 text-gray-500">
          <p>No screenshots available for this execution.</p>
        </div>
      </Card>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pass':
        return 'border-green-500';
      case 'fail':
        return 'border-red-500';
      case 'error':
        return 'border-orange-500';
      case 'skip':
        return 'border-gray-400';
      default:
        return 'border-gray-300';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pass':
        return 'bg-green-100 text-green-700';
      case 'fail':
        return 'bg-red-100 text-red-700';
      case 'error':
        return 'bg-orange-100 text-orange-700';
      case 'skip':
        return 'bg-gray-100 text-gray-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <>
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">Screenshots</h2>
          <span className="text-sm text-gray-600">{screenshots.length} screenshots</span>
        </div>

        {/* Thumbnail Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {screenshots.map((screenshot, index) => (
            <div
              key={index}
              className={`cursor-pointer group relative rounded-lg overflow-hidden border-2 ${getStatusColor(
                screenshot.status
              )} hover:shadow-lg transition-all`}
              onClick={() => setSelectedIndex(index)}
            >
              {/* Screenshot Image */}
              <div className="aspect-video bg-gray-100 relative overflow-hidden">
                <img
                  src={screenshot.path}
                  alt={`Step ${screenshot.stepNumber}`}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                />
                {/* Overlay on hover */}
                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all flex items-center justify-center">
                  <span className="text-white text-4xl opacity-0 group-hover:opacity-100 transition-opacity">
                    🔍
                  </span>
                </div>
              </div>

              {/* Step Info */}
              <div className="p-2 bg-white">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-gray-900">
                    Step {screenshot.stepNumber}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStatusBadge(
                      screenshot.status
                    )}`}
                  >
                    {screenshot.status.toUpperCase()}
                  </span>
                </div>
                <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                  {screenshot.description}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Info Text */}
        <div className="mt-4 text-sm text-gray-500 text-center">
          Click on any screenshot to view full-size with details
        </div>
      </Card>

      {/* Full-Size Modal */}
      {selectedIndex !== null && (
        <ScreenshotModal
          screenshots={screenshots}
          currentIndex={selectedIndex}
          onClose={() => setSelectedIndex(null)}
          onNavigate={setSelectedIndex}
        />
      )}
    </>
  );
}
