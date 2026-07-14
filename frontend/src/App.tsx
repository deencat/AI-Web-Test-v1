import { BrowserRouter, Routes, Route, Navigate, useSearchParams } from 'react-router-dom';
import { EphemeralCredentialProvider } from './context/EphemeralCredentialContext';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { GenerateTestsPage } from './pages/GenerateTestsPage';
import { TestDetailPage } from './pages/TestDetailPage';
import { SavedTestsPage } from './pages/SavedTestsPage';
import TestSuitesPage from './pages/TestSuitesPage';
import { KnowledgeBasePage } from './pages/KnowledgeBasePage';
import { SettingsPage } from './pages/SettingsPage';
import { ExecutionProgressPage } from './pages/ExecutionProgressPage';
import { ExecutionHistoryPage } from './pages/ExecutionHistoryPage';
import { FeedbackListPage } from './pages/FeedbackListPage';
import { DebugSessionPage } from './pages/DebugSessionPage';
import { StepLibraryPage } from './pages/StepLibraryPage';
import { CrawlAndSavePage } from './pages/CrawlAndSavePage';
import './index.css';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = !!localStorage.getItem('token');

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

function TestsRoute() {
  const [searchParams] = useSearchParams();
  const editId = searchParams.get('edit');

  if (editId) {
    return <Navigate to={`/tests/saved?edit=${editId}`} replace />;
  }

  return <GenerateTestsPage />;
}

function App() {
  return (
    <EphemeralCredentialProvider>
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
              <TestsRoute />
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
          path="/step-library"
          element={
            <ProtectedRoute>
              <StepLibraryPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/crawl-and-save"
          element={
            <ProtectedRoute>
              <CrawlAndSavePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/agent-workflow"
          element={<Navigate to="/dashboard" replace />}
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
    </EphemeralCredentialProvider>
  );
}

export default App;
