import React from 'react';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Input } from '../components/common/Input';
import { Button } from '../components/common/Button';

export const SettingsPage: React.FC = () => {
  const userStr = localStorage.getItem('user');
  const user = userStr ? JSON.parse(userStr) : null;

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600 mt-1">Manage your account and preferences</p>
        </div>

        {/* Profile Settings */}
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Profile Information</h2>
          <form className="space-y-4">
            <Input
              label="Full Name"
              type="text"
              defaultValue={user?.full_name || ''}
              placeholder="Enter your full name"
            />
            <Input
              label="Email"
              type="email"
              defaultValue={user?.email || ''}
              placeholder="Enter your email"
            />
            <Input
              label="Username"
              type="text"
              defaultValue={user?.username || ''}
              placeholder="Enter your username"
              disabled
              helperText="Username cannot be changed"
            />
            <div className="flex gap-3">
              <Button variant="primary">Save Changes</Button>
              <Button variant="secondary">Cancel</Button>
            </div>
          </form>
        </Card>

        {/* Password Change */}
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Change Password</h2>
          <form className="space-y-4">
            <Input
              label="Current Password"
              type="password"
              placeholder="Enter current password"
            />
            <Input
              label="New Password"
              type="password"
              placeholder="Enter new password"
            />
            <Input
              label="Confirm New Password"
              type="password"
              placeholder="Confirm new password"
            />
            <Button variant="primary">Update Password</Button>
          </form>
        </Card>

        {/* Preferences */}
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Preferences</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-gray-200">
              <div>
                <p className="font-medium text-gray-900">Email Notifications</p>
                <p className="text-sm text-gray-600">Receive email alerts for test failures</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" defaultChecked />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
              </label>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-gray-200">
              <div>
                <p className="font-medium text-gray-900">Auto-run Tests</p>
                <p className="text-sm text-gray-600">Automatically run tests on schedule</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
              </label>
            </div>
          </div>
        </Card>
      </div>
    </Layout>
  );
};

