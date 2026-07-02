/**
 * QA Factory Connection — orchestrator node URL override (Settings page).
 * Overrides server HERMES_BRIDGE_URL when set.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { Button } from './common/Button';
import { Input } from './common/Input';
import settingsService, { QaFactoryHealth, QaFactorySettings } from '../services/settingsService';
import { FACTORY_PROFILE_DISPLAY_NAMES } from '../constants/factoryProfiles';

interface QaFactoryConnectionSettingsProps {
  canEdit: boolean;
}

export const QaFactoryConnectionSettings: React.FC<QaFactoryConnectionSettingsProps> = ({
  canEdit,
}) => {
  const [settings, setSettings] = useState<QaFactorySettings | null>(null);
  const [orchestratorUrl, setOrchestratorUrl] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [health, setHealth] = useState<QaFactoryHealth | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await settingsService.getQaFactorySettings();
      setSettings(data);
      setOrchestratorUrl(data.orchestrator_bridge_url_override ?? '');
    } catch (err: unknown) {
      setMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to load QA Factory settings',
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load().catch(() => undefined);
  }, [load]);

  const handleSave = async () => {
    if (!canEdit) return;
    setSaving(true);
    setMessage(null);
    try {
      const saved = await settingsService.updateQaFactorySettings({
        orchestrator_bridge_url: orchestratorUrl.trim() || null,
      });
      setSettings(saved);
      setOrchestratorUrl(saved.orchestrator_bridge_url_override ?? '');
      setMessage({ type: 'success', text: 'QA Factory connection saved.' });
      setHealth(null);
    } catch (err: unknown) {
      setMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to save',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleClearOverride = async () => {
    if (!canEdit) return;
    setOrchestratorUrl('');
    setSaving(true);
    setMessage(null);
    try {
      const saved = await settingsService.updateQaFactorySettings({
        orchestrator_bridge_url: null,
      });
      setSettings(saved);
      setMessage({ type: 'success', text: 'Override cleared — using server .env default.' });
      setHealth(null);
    } catch (err: unknown) {
      setMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to clear override',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setHealth(null);
    try {
      const result = await settingsService.checkQaFactoryHealth();
      setHealth(result);
    } catch (err: unknown) {
      setHealth({
        status: 'error',
        message: err instanceof Error ? err.message : 'Health check failed',
      });
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return <p className="text-sm text-gray-500">Loading QA Factory connection…</p>;
  }

  const effective = settings?.effective_bridge_url;
  const envDefault = settings?.env_bridge_url;
  const hasOverride = Boolean(settings?.orchestrator_bridge_url_override);

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">QA Factory Connection</h2>
          <p className="text-sm text-gray-600 mt-1">
            Point Agent Console at your remote <strong>QA Orchestrator</strong> node (the machine
            running the factory bridge on port 8790). When set here, this URL overrides{' '}
            <code className="text-xs bg-gray-100 px-1 rounded">HERMES_BRIDGE_URL</code> in server
            .env.
          </p>
        </div>
        <span
          className={`shrink-0 px-3 py-1 text-xs font-medium rounded-full ${
            effective ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-800'
          }`}
        >
          {effective ? 'Routing enabled' : 'Local worker only'}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
          <p className="text-gray-500 text-xs uppercase tracking-wide">Effective URL</p>
          <p className="font-mono text-gray-900 mt-1 break-all">{effective || '—'}</p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
          <p className="text-gray-500 text-xs uppercase tracking-wide">Server .env default</p>
          <p className="font-mono text-gray-900 mt-1 break-all">{envDefault || '—'}</p>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Orchestrator node URL {hasOverride && <span className="text-green-600">(override active)</span>}
        </label>
        <Input
          type="url"
          placeholder="http://192.168.1.50:8790"
          value={orchestratorUrl}
          onChange={(e) => setOrchestratorUrl(e.target.value)}
          disabled={!canEdit || saving}
        />
        <p className="text-xs text-gray-500 mt-1">
          Use the LAN IP of your Ubuntu factory node — not <code>localhost</code> unless the
          orchestrator runs on this same PC.
        </p>
      </div>

      {!canEdit && (
        <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3">
          Only <code className="bg-white px-1 rounded">superadmin</code> can change the orchestrator
          URL. You can still view the effective connection and test health.
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        {canEdit && (
          <>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? 'Saving…' : 'Save connection'}
            </Button>
            <Button variant="secondary" onClick={handleClearOverride} disabled={saving || !hasOverride}>
              Use .env default
            </Button>
          </>
        )}
        <Button variant="secondary" onClick={handleTest} disabled={testing || !effective}>
          {testing ? 'Testing…' : 'Test connection'}
        </Button>
      </div>

      {message && (
        <p
          className={`text-sm rounded-lg p-3 ${
            message.type === 'success'
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}
        >
          {message.text}
        </p>
      )}

      {health && (
        <div
          className={`text-sm rounded-lg p-3 border ${
            health.status === 'healthy'
              ? 'bg-green-50 border-green-200 text-green-800'
              : 'bg-red-50 border-red-200 text-red-800'
          }`}
        >
          <p className="font-medium capitalize">{health.status}</p>
          {health.message && <p className="mt-1">{health.message}</p>}
          {health.latency_ms != null && (
            <p className="text-xs mt-1 opacity-80">{health.latency_ms} ms</p>
          )}
        </div>
      )}

      <details className="text-sm text-gray-600">
        <summary className="cursor-pointer font-medium text-gray-800">
          Factory specialist agents
        </summary>
        <ul className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-1 pl-4 list-disc">
          {Object.entries(settings?.profile_display_names ?? FACTORY_PROFILE_DISPLAY_NAMES)
            .filter(([key]) => !['factory_bridge', 'hermes_bridge', 'system'].includes(key))
            .map(([id, label]) => (
              <li key={id}>
                <span className="font-medium">{label}</span>
                <span className="text-gray-400 font-mono text-xs ml-1">({id})</span>
              </li>
            ))}
        </ul>
      </details>
    </div>
  );
};

export default QaFactoryConnectionSettings;
