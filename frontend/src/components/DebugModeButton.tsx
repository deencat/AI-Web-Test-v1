/**
 * Debug Mode Button Component
 * 
 * Provides a quick launch button for debug mode from execution pages.
 * Can be embedded in execution history or progress pages.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Bug } from 'lucide-react';

interface DebugModeButtonProps {
  executionId: number;
  targetStepNumber?: number;
  mode?: 'auto' | 'manual';
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const DebugModeButton: React.FC<DebugModeButtonProps> = ({
  executionId,
  targetStepNumber = 1,
  mode = 'auto',
  variant = 'primary',
  size = 'md',
  className = '',
}) => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(`/debug/${executionId}/${targetStepNumber}/${mode}`);
  };

  // Size classes
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  };

  // Variant classes
  const variantClasses = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-gray-600 hover:bg-gray-700 text-white',
    outline: 'border-2 border-blue-600 text-blue-600 hover:bg-blue-50',
  };

  return (
    <button
      onClick={handleClick}
      className={`
        ${sizeClasses[size]}
        ${variantClasses[variant]}
        rounded-lg font-medium transition-colors
        flex items-center gap-2
        ${className}
      `}
      title={`Open debug mode for execution #${executionId} at step ${targetStepNumber}`}
    >
      <Bug className="w-4 h-4" />
      Debug Mode
    </button>
  );
};

export default DebugModeButton;
