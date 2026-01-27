import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { TestsPage } from './pages/TestsPage';
import { TestDetailPage } from './pages/TestDetailPage';
import { SavedTestsPage } from './pages/SavedTestsPage';
import TestSuitesPage from './pages/TestSuitesPage';
import { KnowledgeBasePage } from './pages/KnowledgeBasePage';
import { SettingsPage } from './pages/SettingsPage';
import { ExecutionProgressPage } from './pages/ExecutionProgressPage';
import { ExecutionHistoryPage } from './pages/ExecutionHistoryPage';
import { FeedbackListPage } from './pages/FeedbackListPage';
import { DebugSessionPage } from './pages/DebugSessionPage';
import './index.css';

// Protected Route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = !!localStorage.getItem('token');
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/tests"
          element={
            <ProtectedRoute>
              <TestsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/tests/saved"
          element={
            <ProtectedRoute>
              <SavedTestsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/tests/:testId"
          element={
            <ProtectedRoute>
              <TestDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/test-suites"
          element={
            <ProtectedRoute>
              <TestSuitesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/knowledge-base"
          element={
            <ProtectedRoute>
              <KnowledgeBasePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <SettingsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/executions"
          element={
            <ProtectedRoute>
              <ExecutionHistoryPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/executions/:executionId"
          element={
            <ProtectedRoute>
              <ExecutionProgressPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/debug/:executionId/:targetStep/:mode"
          element={
            <ProtectedRoute>
              <DebugSessionPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/debug/:executionId/:targetStep/:endStep/:mode"
          element={
            <ProtectedRoute>
              <DebugSessionPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/feedback"
          element={
            <ProtectedRoute>
              <FeedbackListPage />
            </ProtectedRoute>
          }
        />
        <Route path="/" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

