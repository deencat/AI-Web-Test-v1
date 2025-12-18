import { useEffect } from 'react';
import { Button } from '../common/Button';

interface ScreenshotModalProps {
  screenshots: Array<{
    path: string;
    stepNumber: number;
    description: string;
    expectedResult?: string;
    actualResult?: string;
    status: 'pass' | 'fail' | 'error' | 'skip' | 'pending' | 'running';
  }>;
  currentIndex: number;
  onClose: () => void;
  onNavigate: (index: number) => void;
}

export function ScreenshotModal({
  screenshots,
  currentIndex,
  onClose,
  onNavigate,
}: ScreenshotModalProps) {
  const currentScreenshot = screenshots[currentIndex];
  const hasPrevious = currentIndex > 0;
  const hasNext = currentIndex < screenshots.length - 1;

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowLeft' && hasPrevious) {
        onNavigate(currentIndex - 1);
      } else if (e.key === 'ArrowRight' && hasNext) {
        onNavigate(currentIndex + 1);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentIndex, hasPrevious, hasNext, onClose, onNavigate]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pass':
        return 'text-green-700';
      case 'fail':
        return 'text-red-700';
      case 'error':
        return 'text-orange-700';
      case 'skip':
        return 'text-gray-700';
      case 'running':
        return 'text-blue-700';
      default:
        return 'text-gray-700';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pass':
        return '✓';
      case 'fail':
        return '✗';
      case 'error':
        return '⚠';
      case 'skip':
        return '○';
      case 'running':
        return '●';
      default:
        return '◷';
    }
  };

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = currentScreenshot.path;
    link.download = `step_${currentScreenshot.stepNumber}_screenshot.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75 p-4"
      onClick={onClose}
    >
      <div
        className="relative bg-white rounded-lg shadow-2xl max-w-6xl w-full max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <span className={`text-2xl font-bold ${getStatusColor(currentScreenshot.status)}`}>
              {getStatusIcon(currentScreenshot.status)}
            </span>
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                Step {currentScreenshot.stepNumber}
              </h2>
              <p className="text-sm text-gray-600">{currentScreenshot.description}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        {/* Screenshot Image */}
        <div className="flex-1 overflow-auto bg-gray-100 p-4 flex items-center justify-center">
          <img
            src={currentScreenshot.path}
            alt={`Step ${currentScreenshot.stepNumber} screenshot`}
            className="max-w-full max-h-full object-contain rounded shadow-lg"
          />
        </div>

        {/* Step Details */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          {currentScreenshot.expectedResult && (
            <div className="mb-2">
              <span className="text-sm font-medium text-gray-700">Expected:</span>
              <p className="text-sm text-gray-600 mt-1">{currentScreenshot.expectedResult}</p>
            </div>
          )}
          {currentScreenshot.actualResult && (
            <div>
              <span className="text-sm font-medium text-gray-700">Actual:</span>
              <p className="text-sm text-gray-600 mt-1">{currentScreenshot.actualResult}</p>
            </div>
          )}
        </div>

        {/* Footer Navigation */}
        <div className="flex items-center justify-between p-4 border-t border-gray-200">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onNavigate(currentIndex - 1)}
            disabled={!hasPrevious}
          >
            ← Previous
          </Button>

          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              {currentIndex + 1} / {screenshots.length}
            </span>
            <Button variant="secondary" size="sm" onClick={handleDownload}>
              ⬇ Download
            </Button>
          </div>

          <Button
            variant="secondary"
            size="sm"
            onClick={() => onNavigate(currentIndex + 1)}
            disabled={!hasNext}
          >
            Next →
          </Button>
        </div>
      </div>
    </div>
  );
}
