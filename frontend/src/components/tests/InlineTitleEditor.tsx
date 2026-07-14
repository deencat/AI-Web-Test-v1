import React, { useState, useRef, useEffect } from 'react';
import { Pencil, Loader2 } from 'lucide-react';
import testsService from '../../services/testsService';

interface InlineTitleEditorProps {
  testId: number;
  title: string;
  onTitleChange: (newTitle: string) => void;
  disabled?: boolean;
}

export const InlineTitleEditor: React.FC<InlineTitleEditorProps> = ({
  testId,
  title,
  onTitleChange,
  disabled = false,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(title);
  const [saving, setSaving] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [errorToast, setErrorToast] = useState<string | null>(null);
  const [successToast, setSuccessToast] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const originalTitleRef = useRef(title);

  useEffect(() => {
    if (!isEditing) {
      setEditValue(title);
      originalTitleRef.current = title;
    }
  }, [title, isEditing]);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const showErrorToast = (msg: string) => {
    setErrorToast(msg || 'Failed to update title');
    setTimeout(() => setErrorToast(null), 4000);
  };

  const showSuccessToast = (msg: string) => {
    setSuccessToast(msg);
    setTimeout(() => setSuccessToast(null), 3000);
  };

  const enterEditMode = () => {
    if (disabled || saving) return;
    setEditValue(title);
    originalTitleRef.current = title;
    setValidationError(null);
    setIsEditing(true);
  };

  const cancelEdit = () => {
    setEditValue(originalTitleRef.current);
    setValidationError(null);
    setIsEditing(false);
  };

  const saveTitle = async () => {
    const trimmed = editValue.trim();

    if (!trimmed) {
      setValidationError('Title is required');
      return;
    }

    if (trimmed === originalTitleRef.current.trim()) {
      setIsEditing(false);
      setValidationError(null);
      return;
    }

    setSaving(true);
    setValidationError(null);

    try {
      await testsService.updateTest(testId.toString(), { title: trimmed });
      originalTitleRef.current = trimmed;
      onTitleChange(trimmed);
      setIsEditing(false);
      showSuccessToast('Title updated');
    } catch (err) {
      setEditValue(originalTitleRef.current);
      setIsEditing(false);
      showErrorToast(
        err instanceof Error ? err.message : 'Failed to update title'
      );
    } finally {
      setSaving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      void saveTitle();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      cancelEdit();
    }
  };

  const handleBlur = () => {
    if (!isEditing || saving) return;
    void saveTitle();
  };

  if (isEditing) {
    return (
      <div className="relative flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={editValue}
            onChange={(e) => {
              setEditValue(e.target.value);
              if (validationError) setValidationError(null);
            }}
            onKeyDown={handleKeyDown}
            onBlur={handleBlur}
            maxLength={255}
            disabled={saving}
            aria-label="Test title"
            aria-invalid={!!validationError}
            aria-describedby={validationError ? `title-error-${testId}` : undefined}
            data-testid={`inline-title-input-${testId}`}
            className={`text-lg font-semibold text-gray-900 border rounded px-2 py-0.5 focus:ring-2 focus:ring-blue-500 focus:outline-none w-full ${
              validationError ? 'border-red-500' : 'border-blue-400'
            } ${saving ? 'opacity-60' : ''}`}
          />
          {saving && <Loader2 className="w-4 h-4 animate-spin text-blue-600 flex-shrink-0" />}
        </div>
        <div aria-live="polite">
          {validationError && (
            <p
              id={`title-error-${testId}`}
              className="text-xs text-red-600 mt-1"
              role="alert"
            >
              {validationError}
            </p>
          )}
          {errorToast && (
            <p className="text-xs text-red-600 mt-1" role="alert">
              {errorToast}
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-w-0 flex-1">
      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={enterEditMode}
          disabled={disabled || saving}
          aria-label={`Edit title: ${title}`}
          data-testid={`inline-title-button-${testId}`}
          className="text-lg font-semibold text-gray-900 hover:text-blue-600 cursor-pointer text-left truncate disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {title}
        </button>
        <button
          type="button"
          onClick={enterEditMode}
          disabled={disabled || saving}
          aria-label="Rename test title"
          data-testid={`inline-title-pencil-${testId}`}
          className="p-1 text-gray-400 hover:text-gray-600 rounded flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Pencil className="w-4 h-4" />
        </button>
        {successToast && (
          <span className="text-xs text-green-600 ml-1 flex-shrink-0" role="status">
            {successToast}
          </span>
        )}
      </div>
      {errorToast && (
        <p className="text-xs text-red-600 mt-1" role="alert" aria-live="polite">
          {errorToast}
        </p>
      )}
    </div>
  );
};
