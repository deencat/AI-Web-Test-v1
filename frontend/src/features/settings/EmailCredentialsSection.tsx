/**
 * EmailCredentialsSection — Sprint 10.10
 *
 * Renders a settings card where users can add, edit, and delete IMAP
 * credentials used by the OTP service during automated test execution.
 */
import React, { useEffect, useState } from 'react';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Card } from '../../components/common/Card';

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1')
  .replace(/\/api\/v1$/, '');

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface EmailCredential {
  id: number;
  label: string;
  imap_host: string;
  imap_port: number;
  email_address: string;
  created_at: string;
  updated_at: string;
}

interface EmailCredentialFormState {
  label: string;
  imap_host: string;
  imap_port: string;
  email_address: string;
  app_password: string;
}

const INITIAL_FORM: EmailCredentialFormState = {
  label: '',
  imap_host: 'imap.gmail.com',
  imap_port: '993',
  email_address: '',
  app_password: '',
};

const KNOWN_IMAP_HOSTS = [
  { label: 'Gmail', host: 'imap.gmail.com' },
  { label: 'Outlook / Office 365', host: 'outlook.office365.com' },
  { label: 'Yahoo', host: 'imap.mail.yahoo.com' },
  { label: 'Custom', host: '' },
];

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------

async function fetchCredentials(token: string): Promise<EmailCredential[]> {
  const resp = await fetch(`${API_BASE_URL}/api/v1/email-credentials`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) throw new Error('Failed to load email credentials');
  return resp.json();
}

async function createCredential(
  token: string,
  body: Omit<EmailCredentialFormState, 'imap_port'> & { imap_port: number }
): Promise<EmailCredential> {
  const resp = await fetch(`${API_BASE_URL}/api/v1/email-credentials`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail ?? 'Failed to create credential');
  }
  return resp.json();
}

async function updateCredential(
  token: string,
  id: number,
  body: Partial<Omit<EmailCredentialFormState, 'imap_port'> & { imap_port: number }>
): Promise<EmailCredential> {
  const resp = await fetch(`${API_BASE_URL}/api/v1/email-credentials/${id}`, {
    method: 'PUT',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail ?? 'Failed to update credential');
  }
  return resp.json();
}

async function deleteCredential(token: string, id: number): Promise<void> {
  const resp = await fetch(`${API_BASE_URL}/api/v1/email-credentials/${id}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) throw new Error('Failed to delete credential');
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface Props {
  token: string;
}

export const EmailCredentialsSection: React.FC<Props> = ({ token }) => {
  const [credentials, setCredentials] = useState<EmailCredential[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<EmailCredentialFormState>(INITIAL_FORM);
  const [isSaving, setIsSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Load credentials on mount
  useEffect(() => {
    load();
  }, []);

  async function load() {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchCredentials(token);
      setCredentials(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setIsLoading(false);
    }
  }

  function openCreateForm() {
    setForm(INITIAL_FORM);
    setEditingId(null);
    setFormError(null);
    setShowForm(true);
  }

  function openEditForm(cred: EmailCredential) {
    setForm({
      label: cred.label,
      imap_host: cred.imap_host,
      imap_port: String(cred.imap_port),
      email_address: cred.email_address,
      app_password: '',
    });
    setEditingId(cred.id);
    setFormError(null);
    setShowForm(true);
  }

  function cancelForm() {
    setShowForm(false);
    setEditingId(null);
    setFormError(null);
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setIsSaving(true);
    setFormError(null);

    const port = parseInt(form.imap_port, 10);
    if (!port || port < 1 || port > 65535) {
      setFormError('IMAP port must be a number between 1 and 65535.');
      setIsSaving(false);
      return;
    }

    try {
      if (editingId !== null) {
        const payload: Record<string, unknown> = {
          label: form.label,
          imap_host: form.imap_host,
          imap_port: port,
          email_address: form.email_address,
        };
        if (form.app_password) payload.app_password = form.app_password;
        await updateCredential(token, editingId, payload);
      } else {
        await createCredential(token, {
          label: form.label,
          imap_host: form.imap_host,
          imap_port: port,
          email_address: form.email_address,
          app_password: form.app_password,
        });
      }
      setShowForm(false);
      setEditingId(null);
      await load();
    } catch (e: any) {
      setFormError(e.message);
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete(id: number) {
    if (!window.confirm('Delete this email credential?')) return;
    try {
      await deleteCredential(token, id);
      setCredentials((prev) => prev.filter((c) => c.id !== id));
    } catch (e: any) {
      setError(e.message);
    }
  }

  function handleImapHostPreset(e: React.ChangeEvent<HTMLSelectElement>) {
    const selected = KNOWN_IMAP_HOSTS.find((h) => h.label === e.target.value);
    if (selected && selected.host) {
      setForm((prev) => ({ ...prev, imap_host: selected.host }));
    }
  }

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Email OTP Credentials</h3>
          <p className="text-sm text-gray-500 mt-1">
            IMAP credentials used to retrieve one-time passwords during test execution.
            Passwords are encrypted at rest.
          </p>
        </div>
        {!showForm && (
          <Button variant="secondary" size="sm" onClick={openCreateForm}>
            + Add Credential
          </Button>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-3 text-red-700 text-sm mb-4">
          {error}
        </div>
      )}

      {/* Credential list */}
      {!isLoading && credentials.length === 0 && !showForm && (
        <p className="text-sm text-gray-400 italic">No email credentials configured.</p>
      )}

      {credentials.map((cred) => (
        <div
          key={cred.id}
          className="flex items-center justify-between py-3 border-b border-gray-100 last:border-none"
        >
          <div>
            <span className="font-medium text-gray-800">{cred.label}</span>
            <span className="ml-2 text-sm text-gray-500">
              {cred.email_address} · {cred.imap_host}:{cred.imap_port}
            </span>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" onClick={() => openEditForm(cred)}>
              Edit
            </Button>
            <Button variant="danger" size="sm" onClick={() => handleDelete(cred.id)}>
              Delete
            </Button>
          </div>
        </div>
      ))}

      {/* Add / Edit form */}
      {showForm && (
        <form onSubmit={handleSave} className="mt-4 space-y-4 border-t border-gray-100 pt-4">
          <h4 className="font-medium text-gray-700">
            {editingId !== null ? 'Edit Credential' : 'New Credential'}
          </h4>

          {formError && (
            <div className="bg-red-50 border border-red-200 rounded p-3 text-red-700 text-sm">
              {formError}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Label"
              placeholder="Gmail QA Account"
              value={form.label}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm((prev) => ({ ...prev, label: e.target.value }))}
              required
            />
            <Input
              label="Email Address"
              type="email"
              placeholder="qa@gmail.com"
              value={form.email_address}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm((prev) => ({ ...prev, email_address: e.target.value }))}
              required
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Provider Preset</label>
              <select
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                defaultValue=""
                onChange={handleImapHostPreset}
              >
                <option value="" disabled>Select preset…</option>
                {KNOWN_IMAP_HOSTS.map((h) => (
                  <option key={h.label} value={h.label}>{h.label}</option>
                ))}
              </select>
            </div>
            <Input
              label="IMAP Host"
              placeholder="imap.gmail.com"
              value={form.imap_host}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm((prev) => ({ ...prev, imap_host: e.target.value }))}
              required
            />
            <Input
              label="IMAP Port"
              type="number"
              min="1"
              max="65535"
              placeholder="993"
              value={form.imap_port}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm((prev) => ({ ...prev, imap_port: e.target.value }))}
              required
            />
          </div>

          <Input
            label={editingId !== null ? 'App Password (leave blank to keep existing)' : 'App Password'}
            type="password"
            placeholder="xxxx-xxxx-xxxx-xxxx"
            value={form.app_password}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm((prev) => ({ ...prev, app_password: e.target.value }))}
            required={editingId === null}
          />

          <div className="flex gap-3">
            <Button type="submit" loading={isSaving}>
              {editingId !== null ? 'Save Changes' : 'Add Credential'}
            </Button>
            <Button type="button" variant="secondary" onClick={cancelForm} disabled={isSaving}>
              Cancel
            </Button>
          </div>
        </form>
      )}
    </Card>
  );
};
