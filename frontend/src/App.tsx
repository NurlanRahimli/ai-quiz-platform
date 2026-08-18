import { Navigate, Route, Routes } from "react-router-dom"

import ProtectedRoute from "./auth/ProtectedRoute"
import LoginPage from "./pages/auth/LoginPage"
import RegisterPage from "./pages/auth/RegisterPage"
import DashboardPage from "./pages/dashboard/DashboardPage"
import CreateQuizPage from "./pages/quizzes/CreateQuizPage"
import EditQuizPage from "./pages/quizzes/EditQuizPage"
import TakeQuizPage from "./pages/quizzes/TakeQuizPage"

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/register" replace />} />

      <Route path="/register" element={<RegisterPage />} />
      <Route path="/login" element={<LoginPage />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/quizzes/new" element={<CreateQuizPage />} />
        <Route path="/quizzes/:quizId" element={<EditQuizPage />} />
        <Route path="/quizzes/:quizId/take" element={<TakeQuizPage />} />
      </Route>
    </Routes>
  )
}

export default App