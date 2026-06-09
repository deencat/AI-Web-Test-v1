'use client';

import React from 'react';
import { Trash2 } from 'lucide-react';
import type { AvailableProvider, CustomModelEntry } from '../types/api';

export interface CustomModelsPanelProps {
  customModels: Record<string, CustomModelEntry[]>;
  providers: AvailableProvider[];
  onRemove: (provider: string, modelId: string) => void;
}

/**
 * Mini-panel listing saved custom models per provider with delete actions (Sprint 10.20).
 */
export const CustomModelsPanel: React.FC<CustomModelsPanelProps> = ({
  customModels,
  providers,
  onRemove,
}) => {
  const entries = Object.entries(customModels).flatMap(([provider, models]) =>
    models.map((entry) => ({ provider, entry })),
  );

  if (entries.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-gray-200 p-4 text-sm text-gray-500">
        No saved custom models yet. Use &quot;⚙ Custom model...&quot; in any provider dropdown to add one.
      </div>
    );
  }

  const providerLabel = (name: string) =>
    providers.find((p) => p.name === name)?.display_name ?? name;

  return (
    <div className="space-y-2">
      {entries.map(({ provider, entry }) => (
        <div
          key={`${provider}-${entry.id}`}
          className="flex items-center justify-between gap-3 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2"
        >
          <div className="min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">
              {entry.display_name || entry.id}
            </p>
            <p className="text-xs text-gray-500">
              {providerLabel(provider)} · <span className="font-mono">{entry.id}</span>
            </p>
          </div>
          <button
            type="button"
            aria-label={`Remove ${entry.id}`}
            onClick={() => onRemove(provider, entry.id)}
            className="shrink-0 rounded p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-600 transition-colors"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
};

export default CustomModelsPanel;
