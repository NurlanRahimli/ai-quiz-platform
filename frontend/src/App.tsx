import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/useAuth";

import ProtectedRoute from "./auth/ProtectedRoute";
import AppShell from "./components/layout/AppShell";

import LoginPage from "./pages/auth/LoginPage";
import RegisterPage from "./pages/auth/RegisterPage";
import VerifyEmailPage from "./pages/auth/VerifyEmailPage";
import DashboardPage from "./pages/dashboard/DashboardPage";
import CreateQuizPage from "./pages/quizzes/CreateQuizPage";
import EditQuizPage from "./pages/quizzes/EditQuizPage";
import TakeQuizPage from "./pages/quizzes/TakeQuizPage";
import QuizResultsPage from "./pages/quizzes/QuizResultsPage";
import QuizAttemptHistoryPage from "./pages/quizzes/QuizAttemptHistoryPage";
import QuizDetailsPage from "./pages/quizzes/QuizDetailsPage";
import ProfilePage from "./pages/profile/ProfilePage";
import DiscoverQuizzesPage from "./pages/quizzes/DiscoverQuizzesPage";
import SearchQuizzesPage from "./pages/quizzes/SearchQuizzesPage";
import PublicProfilePage from "./pages/profile/PublicProfilePage"
import AuditLogPage from "./pages/audit/AuditLogPage";
import MyAttemptsPage from "./pages/attempts/MyAttemptsPage";
import ImportQuizPage from "./pages/quizzes/ImportQuizPage";
import SettingsPage from "./pages/settings/SettingsPage";


function QuizDetailsLayout() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return null;
  }

  if (isAuthenticated) {
    return (
      <AppShell>
        <QuizDetailsPage />
      </AppShell>
    );
  }

  return <QuizDetailsPage />;
}


function ProtectedAppLayout() {
  return (
    <AppShell>
      <Routes>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route
          path="/import-quiz"
          element={<ImportQuizPage />}
        />
        <Route path="/quizzes/edit/:quizId" element={<EditQuizPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/audit-log" element={<AuditLogPage />} />
        <Route path="/attempts" element={<MyAttemptsPage />} />
        <Route
          path="/quizzes/:quizId/attempts/:attemptId/results"
          element={<QuizResultsPage />}
        />
        <Route
          path="/quizzes/:quizId/history"
          element={<QuizAttemptHistoryPage />}
        />
        <Route path="/discover" element={<DiscoverQuizzesPage />} />
        <Route
          path="/discover/search"
          element={<SearchQuizzesPage />}
        />
        <Route
          path="/users/:userId"
          element={<PublicProfilePage />}
        />
      </Routes>
    </AppShell>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/register" replace />} />

      <Route path="/register" element={<RegisterPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/quizzes/:quizId/take" element={<TakeQuizPage />} />
      <Route
        path="/quizzes/:quizId/guest-results"
        element={<QuizResultsPage />}
      />
      <Route
        path="/quizzes/:quizId"
        element={<QuizDetailsLayout />}
      />
      <Route element={<ProtectedRoute />}>
        <Route
          path="/quizzes/new"
          element={
            <AppShell>
              <CreateQuizPage />
            </AppShell>
          }
        />

        <Route path="/*" element={<ProtectedAppLayout />} />
      </Route>



      <Route element={<ProtectedRoute />}>
        <Route path="/*" element={<ProtectedAppLayout />} />
      </Route>
    </Routes>
  );
}

export default App;