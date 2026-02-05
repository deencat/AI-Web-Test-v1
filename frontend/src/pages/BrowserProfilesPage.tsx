/**
 * Browser Profiles Management Page
 * Created: February 3, 2026
 * Purpose: Manage browser profiles for session persistence
 */

import React, { useState, useEffect } from 'react';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Plus, Edit2, Trash2, Download, Upload, RefreshCw, Play, ExternalLink, Copy, Lock } from 'lucide-react';
import browserProfileService from '../services/browserProfileService';
import debugService from '../services/debugService';
import type { BrowserProfile, BrowserProfileFormData } from '../types/browserProfile';
import { OS_TYPES, BROWSER_TYPES } from '../types/browserProfile';

export const BrowserProfilesPage: React.FC = () => {
  // Data state
  const [profiles, setProfiles] = useState<BrowserProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // UI state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  
  // Form state
  const [formData, setFormData] = useState<BrowserProfileFormData>({
    profile_name: '',
    os_type: 'windows',
    browser_type: 'chromium',
    description: '',
    http_username: '',
    http_password: ''
  });
  const [editingProfile, setEditingProfile] = useState<BrowserProfile | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [clearHttpCredentials, setClearHttpCredentials] = useState(false);
  
  // Export state
  const [exportProfileId, setExportProfileId] = useState<number | null>(null);
  const [sessionId, setSessionId] = useState('');
  const [exporting, setExporting] = useState(false);
  const [showInstructions, setShowInstructions] = useState(true);
  const [startingBrowser, setStartingBrowser] = useState(false);
  
  // Upload state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  // Load profiles on mount
  useEffect(() => {
    loadProfiles();
  }, []);

  const loadProfiles = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await browserProfileService.getAllProfiles();
      setProfiles(response.profiles);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load profiles');
      console.error('Failed to load profiles:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      setError(null);
      
      await browserProfileService.createProfile({
        profile_name: formData.profile_name,
        os_type: formData.os_type as 'windows' | 'linux' | 'macos',
        browser_type: formData.browser_type as 'chromium' | 'firefox' | 'webkit',
        description: formData.description || undefined,
        http_username: formData.http_username || undefined,
        http_password: formData.http_password || undefined
      });
      
      setShowCreateModal(false);
      setFormData({
        profile_name: '',
        os_type: 'windows',
        browser_type: 'chromium',
        description: '',
        http_username: '',
        http_password: ''
      });
      setClearHttpCredentials(false);
      await loadProfiles();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create profile');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (profile: BrowserProfile) => {
    setEditingProfile(profile);
    setFormData({
      profile_name: profile.profile_name,
      os_type: profile.os_type,
      browser_type: profile.browser_type,
      description: profile.description || '',
      http_username: profile.http_username || '',
      http_password: ''
    });
    setClearHttpCredentials(false);
    setShowEditModal(true);
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProfile) return;
    
    try {
      setSubmitting(true);
      setError(null);
      
      await browserProfileService.updateProfile(editingProfile.id, {
        profile_name: formData.profile_name,
        os_type: formData.os_type as 'windows' | 'linux' | 'macos',
        browser_type: formData.browser_type as 'chromium' | 'firefox' | 'webkit',
        description: formData.description || undefined,
        http_username: formData.http_username || undefined,
        http_password: formData.http_password || undefined,
        clear_http_credentials: clearHttpCredentials
      });
      
      setShowEditModal(false);
      setEditingProfile(null);
  setClearHttpCredentials(false);
      await loadProfiles();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (profileId: number) => {
    if (!confirm('Are you sure you want to delete this profile?')) return;
    
    try {
      setError(null);
      await browserProfileService.deleteProfile(profileId);
      await loadProfiles();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete profile');
    }
  };

  const handleExport = (profile: BrowserProfile) => {
    setExportProfileId(profile.id);
    setSessionId('');
    setShowExportModal(true);
  };

  const handleStartBrowser = async () => {
    try {
      setStartingBrowser(true);
      setError(null);
      
      const response = await debugService.startStandaloneBrowser('chromium', false);
      
      setSessionId(response.session_id);
      
      alert(`✅ Browser started successfully!\n\nSession ID: ${response.session_id}\n\nA browser window has opened. Please:\n1. Navigate to your website\n2. Log in with your credentials\n3. Browse around to generate session data\n4. Come back here and click "Export & Download"\n\n⚠️ Keep the browser window open!`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start browser');
    } finally {
      setStartingBrowser(false);
    }
  };

  const handleExportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!exportProfileId) return;
    
    try {
      setExporting(true);
      setError(null);
      
      const blob = await browserProfileService.exportProfile(exportProfileId, sessionId);
      const profile = profiles.find(p => p.id === exportProfileId);
      const filename = profile ? browserProfileService.getProfileFilename(profile) : `profile_${exportProfileId}.zip`;
      
      browserProfileService.downloadProfileBlob(blob, filename);
      
      setShowExportModal(false);
      setExportProfileId(null);
      setSessionId('');
      await loadProfiles(); // Refresh to update last_sync_at
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export profile');
    } finally {
      setExporting(false);
    }
  };

  const handleUpload = async () => {
    if (!uploadFile) return;
    
    try {
      setUploading(true);
      setError(null);
      
      const response = await browserProfileService.uploadProfile(uploadFile);
      
      alert(`Profile uploaded successfully! ${response.profile_data.cookies.length} cookies, ${Object.keys(response.profile_data.localStorage).length} localStorage items.`);
      
      setShowUploadModal(false);
      setUploadFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload profile');
    } finally {
      setUploading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setUploadFile(e.dataTransfer.files[0]);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="p-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Browser Profiles
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage browser session profiles for cross-platform testing
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="mb-6 flex gap-3">
          <Button
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Profile
          </Button>
          <Button
            onClick={() => setShowUploadModal(true)}
            className="bg-green-600 hover:bg-green-700 text-white"
          >
            <Upload className="w-4 h-4 mr-2" />
            Upload Profile
          </Button>
          <Button
            onClick={loadProfiles}
            className="bg-gray-600 hover:bg-gray-700 text-white"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>

        {/* Profiles List */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {profiles.length === 0 ? (
            <Card className="col-span-full p-8 text-center">
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                No profiles yet. Create your first profile to get started.
              </p>
              <Button onClick={() => setShowCreateModal(true)} className="bg-blue-600 hover:bg-blue-700 text-white">
                <Plus className="w-4 h-4 mr-2" />
                Create First Profile
              </Button>
            </Card>
          ) : (
            profiles.map((profile) => (
              <Card key={profile.id} className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                      {profile.profile_name}
                    </h3>
                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                      <span>{browserProfileService.getOSIcon(profile.os_type)} {profile.os_type}</span>
                      <span>•</span>
                      <span>{browserProfileService.getBrowserIcon(profile.browser_type)} {profile.browser_type}</span>
                    </div>
                    {profile.has_http_credentials && (
                      <div className="mt-2 inline-flex items-center gap-1 text-xs text-green-700 dark:text-green-300 bg-green-100 dark:bg-green-900/30 px-2 py-1 rounded">
                        <Lock className="w-3 h-3" />
                        HTTP Auth: {profile.http_username || 'configured'}
                      </div>
                    )}
                  </div>
                </div>

                {profile.description && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    {profile.description}
                  </p>
                )}

                <div className="text-xs text-gray-500 dark:text-gray-500 mb-3">
                  <div>Created: {browserProfileService.formatDate(profile.created_at)}</div>
                  <div>Last Sync: {browserProfileService.formatDate(profile.last_sync_at)}</div>
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={() => handleEdit(profile)}
                    className="flex-1 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300"
                  >
                    <Edit2 className="w-4 h-4 mr-1" />
                    Edit
                  </Button>
                  <Button
                    onClick={() => handleExport(profile)}
                    className="flex-1 bg-blue-100 hover:bg-blue-200 dark:bg-blue-900 dark:hover:bg-blue-800 text-blue-700 dark:text-blue-300"
                  >
                    <Download className="w-4 h-4 mr-1" />
                    Export
                  </Button>
                  <Button
                    onClick={() => handleDelete(profile.id)}
                    className="bg-red-100 hover:bg-red-200 dark:bg-red-900 dark:hover:bg-red-800 text-red-700 dark:text-red-300"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </Card>
            ))
          )}
        </div>

        {/* Create Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <Card className="w-full max-w-md p-6">
              <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">Create Profile</h2>
              <form onSubmit={handleCreate}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
                      Profile Name *
                    </label>
                    <input
                      type="text"
                      value={formData.profile_name}
                      onChange={(e) => setFormData({...formData, profile_name: e.target.value})}
                      className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                      required
                      placeholder="e.g., Windows 11 - Admin Session"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
                      Operating System *
                    </label>
                    <select
                      value={formData.os_type}
                      onChange={(e) => setFormData({...formData, os_type: e.target.value})}
                      className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                      required
                    >
                      {OS_TYPES.map(os => (
                        <option key={os.value} value={os.value}>
                          {os.icon} {os.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
                      Browser Type *
                    </label>
                    <select
                      value={formData.browser_type}
                      onChange={(e) => setFormData({...formData, browser_type: e.target.value})}
                      className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                      required
                    >
                      {BROWSER_TYPES.map(browser => (
                        <option key={browser.value} value={browser.value}>
                          {browser.icon} {browser.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
                      Description
                    </label>
                    <textarea
                      value={formData.description}
                      onChange={(e) => setFormData({...formData, description: e.target.value})}
                      className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                      rows={3}
                      placeholder="Optional description"
                    />
                  </div>

                  <div className="border-t pt-4">
                    <div className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      <Lock className="w-4 h-4" />
                      HTTP Basic Auth (Optional)
                    </div>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-1">
                          Username
                        </label>
                        <input
                          type="text"
                          value={formData.http_username}
                          onChange={(e) => setFormData({...formData, http_username: e.target.value})}
                          className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                          placeholder="basic-auth-user"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-1">
                          Password
                        </label>
                        <input
                          type="password"
                          value={formData.http_password}
                          onChange={(e) => setFormData({...formData, http_password: e.target.value})}
                          className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                          placeholder="••••••••"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3 mt-6">
                  <Button type="submit" disabled={submitting} className="flex-1 bg-blue-600 hover:bg-blue-700 text-white">
                    {submitting ? 'Creating...' : 'Create Profile'}
                  </Button>
                  <Button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="flex-1 bg-gray-300 hover:bg-gray-400 dark:bg-gray-600 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-200"
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            </Card>
          </div>
        )}

        {/* Edit Modal */}
        {showEditModal && editingProfile && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <Card className="w-full max-w-md p-6">
              <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">Edit Profile</h2>
              <form onSubmit={handleUpdate}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
                      Profile Name *
                    </label>
                    <input
                      type="text"
                      value={formData.profile_name}
                      onChange={(e) => setFormData({...formData, profile_name: e.target.value})}
                      className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
                      Operating System *
                    </label>
                    <select
                      value={formData.os_type}
                      onChange={(e) => setFormData({...formData, os_type: e.target.value})}
                      className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                      required
                    >
                      {OS_TYPES.map(os => (
                        <option key={os.value} value={os.value}>
                          {os.icon} {os.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
                      Browser Type *
                    </label>
                    <select
                      value={formData.browser_type}
                      onChange={(e) => setFormData({...formData, browser_type: e.target.value})}
                      className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                      required
                    >
                      {BROWSER_TYPES.map(browser => (
                        <option key={browser.value} value={browser.value}>
                          {browser.icon} {browser.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
                      Description
                    </label>
                    <textarea
                      value={formData.description}
                      onChange={(e) => setFormData({...formData, description: e.target.value})}
                      className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                      rows={3}
                    />
                  </div>

                  <div className="border-t pt-4">
                    <div className="flex items-center justify-between text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      <span className="flex items-center gap-2">
                        <Lock className="w-4 h-4" />
                        HTTP Basic Auth (Optional)
                      </span>
                      {editingProfile.has_http_credentials && (
                        <span className="text-xs text-green-600 dark:text-green-400">
                          Configured
                        </span>
                      )}
                    </div>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-1">
                          Username
                        </label>
                        <input
                          type="text"
                          value={formData.http_username}
                          onChange={(e) => setFormData({...formData, http_username: e.target.value})}
                          className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                          placeholder="basic-auth-user"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-1">
                          Password
                        </label>
                        <input
                          type="password"
                          value={formData.http_password}
                          onChange={(e) => setFormData({...formData, http_password: e.target.value})}
                          className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                          placeholder="Leave blank to keep existing"
                        />
                      </div>
                      <label className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-300">
                        <input
                          type="checkbox"
                          checked={clearHttpCredentials}
                          onChange={(e) => setClearHttpCredentials(e.target.checked)}
                          className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                        />
                        Clear stored HTTP credentials
                      </label>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3 mt-6">
                  <Button type="submit" disabled={submitting} className="flex-1 bg-blue-600 hover:bg-blue-700 text-white">
                    {submitting ? 'Updating...' : 'Update Profile'}
                  </Button>
                  <Button
                    type="button"
                    onClick={() => {
                      setShowEditModal(false);
                      setEditingProfile(null);
                      setClearHttpCredentials(false);
                    }}
                    className="flex-1 bg-gray-300 hover:bg-gray-400 dark:bg-gray-600 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-200"
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            </Card>
          </div>
        )}

        {/* Export Modal */}
        {showExportModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
              <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">Export Browser Profile</h2>
              
              {/* Quick Action: Start Browser */}
              <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                <h3 className="font-semibold text-green-900 dark:text-green-100 mb-2">🚀 Quick Start (Recommended)</h3>
                <p className="text-sm text-green-800 dark:text-green-200 mb-3">
                  Click the button below to start a browser session. No API knowledge needed!
                </p>
                <Button
                  onClick={handleStartBrowser}
                  disabled={startingBrowser}
                  className="w-full bg-green-600 hover:bg-green-700 text-white flex items-center justify-center gap-2"
                >
                  {startingBrowser ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Starting Browser...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      Start Browser Session
                    </>
                  )}
                </Button>
                {sessionId && (
                  <div className="mt-3 p-2 bg-white dark:bg-gray-800 rounded border border-green-300 dark:border-green-700">
                    <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Session ID:</p>
                    <code className="text-sm text-green-700 dark:text-green-300 font-mono">{sessionId}</code>
                  </div>
                )}
              </div>
              
              {/* Step-by-Step Instructions */}
              {showInstructions && (
                <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold text-blue-900 dark:text-blue-100">📋 Alternative: Use Swagger UI</h3>
                    <button
                      onClick={() => setShowInstructions(false)}
                      className="text-blue-600 dark:text-blue-400 text-sm hover:underline"
                    >
                      Hide Instructions
                    </button>
                  </div>
                  <p className="text-xs text-blue-700 dark:text-blue-300 mb-2">
                    For advanced users who want to use Swagger UI directly:
                  </p>
                  <ol className="text-sm text-blue-800 dark:text-blue-200 space-y-3 mt-3">
                    <li className="flex gap-2">
                      <span className="font-bold min-w-[24px]">1.</span>
                      <div>
                        <strong>Open Swagger UI in a new tab:</strong>
                        <a 
                          href="http://localhost:8000/docs" 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="ml-2 text-blue-600 dark:text-blue-400 hover:underline inline-flex items-center gap-1"
                        >
                          http://localhost:8000/docs
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                    </li>
                    <li className="flex gap-2">
                      <span className="font-bold min-w-[24px]">2.</span>
                      <div>
                        <strong>Authenticate in Swagger:</strong>
                        <ul className="list-disc list-inside ml-4 mt-1">
                          <li>Click the green "Authorize" button at the top</li>
                          <li>Enter your token: <code className="bg-blue-100 dark:bg-blue-800 px-1 rounded">Bearer YOUR_TOKEN</code></li>
                          <li>Click "Authorize" then "Close"</li>
                        </ul>
                      </div>
                    </li>
                    <li className="flex gap-2">
                      <span className="font-bold min-w-[24px]">3.</span>
                      <div>
                        <strong>Start a Debug Session:</strong>
                        <ul className="list-disc list-inside ml-4 mt-1">
                          <li>Find <code className="bg-blue-100 dark:bg-blue-800 px-1 rounded">POST /api/v1/debug/start</code></li>
                          <li>Click "Try it out"</li>
                          <li>Use this request body:</li>
                        </ul>
                        <div className="mt-2 p-2 bg-gray-800 text-green-400 rounded text-xs font-mono relative">
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(JSON.stringify({
                                execution_id: 1,
                                target_step_number: 1,
                                mode: "manual"
                              }, null, 2));
                              alert('Copied to clipboard!');
                            }}
                            className="absolute top-2 right-2 text-gray-400 hover:text-white"
                            title="Copy to clipboard"
                          >
                            <Copy className="w-4 h-4" />
                          </button>
                          <pre className="whitespace-pre-wrap">{`{
  "execution_id": 1,
  "target_step_number": 1,
  "mode": "manual"
}`}</pre>
                        </div>
                        <p className="text-xs mt-1 text-blue-700 dark:text-blue-300">
                          ℹ️ This starts a browser without executing any steps. The execution_id can be any existing execution.
                        </p>
                      </div>
                    </li>
                    <li className="flex gap-2">
                      <span className="font-bold min-w-[24px]">4.</span>
                      <div>
                        <strong>Log in manually:</strong>
                        <ul className="list-disc list-inside ml-4 mt-1">
                          <li>A browser window will open automatically</li>
                          <li>Navigate to your target website</li>
                          <li>Log in with your credentials</li>
                          <li>Browse around to generate session data</li>
                          <li><strong className="text-red-600 dark:text-red-400">KEEP THE BROWSER WINDOW OPEN!</strong></li>
                        </ul>
                      </div>
                    </li>
                    <li className="flex gap-2">
                      <span className="font-bold min-w-[24px]">5.</span>
                      <div>
                        <strong>Copy the session_id:</strong>
                        <ul className="list-disc list-inside ml-4 mt-1">
                          <li>From the Swagger response, copy the <code className="bg-blue-100 dark:bg-blue-800 px-1 rounded">session_id</code></li>
                          <li>It looks like: <code className="bg-blue-100 dark:bg-blue-800 px-1 rounded">debug_abc123def456</code></li>
                          <li>Paste it in the field below</li>
                        </ul>
                      </div>
                    </li>
                    <li className="flex gap-2">
                      <span className="font-bold min-w-[24px]">6.</span>
                      <div>
                        <strong>Click "Export & Download" below</strong> to capture and download your session
                      </div>
                    </li>
                  </ol>
                </div>
              )}

              {!showInstructions && (
                <button
                  onClick={() => setShowInstructions(true)}
                  className="mb-4 text-blue-600 dark:text-blue-400 text-sm hover:underline"
                >
                  📋 Show Instructions
                </button>
              )}

              <form onSubmit={handleExportSubmit}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
                      Debug Session ID *
                    </label>
                    <input
                      type="text"
                      value={sessionId}
                      onChange={(e) => setSessionId(e.target.value)}
                      className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                      required
                      placeholder="e.g., debug_abc123def456"
                    />
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Get this from the Swagger UI response after starting a debug session
                    </p>
                  </div>
                </div>

                <div className="flex gap-3 mt-6">
                  <Button type="submit" disabled={exporting} className="flex-1 bg-green-600 hover:bg-green-700 text-white">
                    {exporting ? 'Exporting...' : 'Export & Download'}
                  </Button>
                  <Button
                    type="button"
                    onClick={() => {
                      setShowExportModal(false);
                      setExportProfileId(null);
                      setSessionId('');
                      setShowInstructions(true);
                    }}
                    className="flex-1 bg-gray-300 hover:bg-gray-400 dark:bg-gray-600 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-200"
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            </Card>
          </div>
        )}

        {/* Upload Modal */}
        {showUploadModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <Card className="w-full max-w-md p-6">
              <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">Upload Profile</h2>
              <div className="mb-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                <p className="text-sm text-green-800 dark:text-green-200">
                  Upload a previously exported profile ZIP file. The profile data will be parsed and ready to use in test execution.
                </p>
              </div>

              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center ${
                  dragActive
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-300 dark:border-gray-600'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <p className="text-gray-600 dark:text-gray-400 mb-2">
                  {uploadFile ? uploadFile.name : 'Drag & drop profile ZIP file here'}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-500 mb-4">or</p>
                <label className="cursor-pointer">
                  <span className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded">
                    Browse Files
                  </span>
                  <input
                    type="file"
                    accept=".zip"
                    className="hidden"
                    onChange={(e) => e.target.files && setUploadFile(e.target.files[0])}
                  />
                </label>
              </div>

              <div className="flex gap-3 mt-6">
                <Button
                  onClick={handleUpload}
                  disabled={!uploadFile || uploading}
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white disabled:opacity-50"
                >
                  {uploading ? 'Uploading...' : 'Upload Profile'}
                </Button>
                <Button
                  onClick={() => {
                    setShowUploadModal(false);
                    setUploadFile(null);
                  }}
                  className="flex-1 bg-gray-300 hover:bg-gray-400 dark:bg-gray-600 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-200"
                >
                  Cancel
                </Button>
              </div>
            </Card>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default BrowserProfilesPage;
