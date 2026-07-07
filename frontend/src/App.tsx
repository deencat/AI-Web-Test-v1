import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { EphemeralCredentialProvider } from './context/EphemeralCredentialContext';
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
import { AgentWorkflowPage } from './pages/AgentWorkflowPage';
import { AgentConsolePage } from './pages/AgentConsolePage';
import { JourneyRegistryPage } from './pages/JourneyRegistryPage';
import { BacklogQueuePage } from './pages/BacklogQueuePage';
import { HealReviewPage } from './pages/HealReviewPage';
import { StepLibraryPage } from './pages/StepLibraryPage';
import { CrawlAndSavePage } from './pages/CrawlAndSavePage';
import { ProductsListPage } from './pages/ProductsListPage';
import { ProductWorkspacePage } from './pages/ProductWorkspacePage';
import { ProgramsListPage } from './pages/ProgramsListPage';
import { ProgramHubPage } from './pages/ProgramHubPage';
import { InitiativeDetailPage } from './pages/InitiativeDetailPage';
import { ProgramManifestEditorPage } from './pages/ProgramManifestEditorPage';
import './index.css';

// Protected Route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = !!localStorage.getItem('token');
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
}

// Admin-only route guard (UF-5)
function AdminRoute({ children }: { children: React.ReactNode }) {
  const role = (() => {
    try {
      const raw = localStorage.getItem('user');
      if (!raw) return 'user';
      return ((JSON.parse(raw) as { role?: string }).role || 'user').toLowerCase();
    } catch {
      return 'user';
    }
  })();
  if (role !== 'admin' && role !== 'superadmin') {
    return <Navigate to="/products" replace />;
  }
  return <>{children}</>;
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
          element={
            <ProtectedRoute>
              <AgentWorkflowPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/agent-console"
          element={
            <ProtectedRoute>
              <AgentConsolePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/journey-registry"
          element={
            <ProtectedRoute>
              <AdminRoute>
                <JourneyRegistryPage />
              </AdminRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/backlog"
          element={
            <ProtectedRoute>
              <AdminRoute>
                <BacklogQueuePage />
              </AdminRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/heal-review"
          element={
            <ProtectedRoute>
              <HealReviewPage />
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
        <Route
          path="/products"
          element={
            <ProtectedRoute>
              <ProductsListPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/products/:productId"
          element={
            <ProtectedRoute>
              <ProductWorkspacePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/programs"
          element={
            <ProtectedRoute>
              <AdminRoute>
                <ProgramsListPage />
              </AdminRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/programs/:slug"
          element={
            <ProtectedRoute>
              <AdminRoute>
                <ProgramHubPage />
              </AdminRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/programs/:slug/initiatives/:initiativeId"
          element={
            <ProtectedRoute>
              <AdminRoute>
                <InitiativeDetailPage />
              </AdminRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/programs/:slug/edit"
          element={
            <ProtectedRoute>
              <AdminRoute>
                <ProgramManifestEditorPage />
              </AdminRoute>
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

