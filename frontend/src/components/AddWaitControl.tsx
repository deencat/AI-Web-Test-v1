import React, { useState } from 'react';

const PRESETS = [1, 2, 5, 10, 30, 60] as const;
const MAX_SECONDS = 120;
const MIN_SECONDS = 1;

export interface AddWaitControlProps {
  onInsert: (line: string) => void;
}

/**
 * Compact duration picker that inserts a canonical timed-wait step line
 * (`wait: Ns`) into the steps list — not a loop-block / wait_blocks editor.
 */
export const AddWaitControl: React.FC<AddWaitControlProps> = ({ onInsert }) => {
  const [open, setOpen] = useState(false);
  const [custom, setCustom] = useState('');
  const [error, setError] = useState<string | null>(null);

  const insertSeconds = (seconds: number) => {
    const clamped = Math.min(MAX_SECONDS, Math.max(MIN_SECONDS, Math.round(seconds)));
    if (seconds > MAX_SECONDS) {
      setError('Max 120 seconds');
      onInsert(`wait: ${clamped}s`);
      setCustom(String(clamped));
      return;
    }
    if (seconds < MIN_SECONDS) {
      setError('Min 1 second');
      return;
    }
    setError(null);
    onInsert(`wait: ${clamped}s`);
    setOpen(false);
    setCustom('');
  };

  const handleCustomConfirm = () => {
    const n = Number(custom);
    if (!custom.trim() || Number.isNaN(n)) {
      setError('Enter a duration in seconds');
      return;
    }
    insertSeconds(n);
  };

  return (
    <div className="relative inline-block">
      <button
        type="button"
        data-testid="add-wait-button"
        onClick={() => {
          setOpen((v) => !v);
          setError(null);
        }}
        className="px-3 py-1 text-sm border border-slate-500 text-slate-600 rounded hover:bg-slate-100"
        title="Insert a timed wait step"
      >
        + Add Wait
      </button>

      {open && (
        <div
          data-testid="add-wait-duration"
          className="absolute right-0 z-20 mt-1 w-56 rounded border border-slate-300 bg-white p-3 shadow-sm"
        >
          <div className="mb-2 text-xs font-medium text-slate-700">Wait duration</div>
          <div className="mb-2 flex flex-wrap gap-1">
            {PRESETS.map((s) => (
              <button
                key={s}
                type="button"
                data-testid={`add-wait-preset-${s}`}
                onClick={() => insertSeconds(s)}
                className="rounded border border-slate-300 px-2 py-0.5 text-xs text-slate-700 hover:bg-slate-50"
              >
                {s}s
              </button>
            ))}
          </div>
          <div className="flex items-center gap-1">
            <input
              type="number"
              min={MIN_SECONDS}
              max={MAX_SECONDS}
              value={custom}
              data-testid="add-wait-custom-input"
              onChange={(e) => {
                setCustom(e.target.value);
                setError(null);
              }}
              placeholder="Custom (1–120)"
              className="w-full rounded border border-slate-300 px-2 py-1 text-xs"
            />
            <button
              type="button"
              data-testid="add-wait-custom-confirm"
              onClick={handleCustomConfirm}
              disabled={!custom.trim()}
              className="shrink-0 rounded border border-slate-500 px-2 py-1 text-xs text-slate-700 hover:bg-slate-50 disabled:opacity-40"
            >
              Insert
            </button>
          </div>
          {error && (
            <div data-testid="add-wait-error" className="mt-1 text-xs text-red-600">
              {error}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AddWaitControl;
