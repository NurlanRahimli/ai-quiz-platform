import { Navigate, Route, Routes } from "react-router-dom"

import RegisterPage from "./pages/auth/RegisterPage"

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/register" replace />} />
      <Route path="/register" element={<RegisterPage />} />
    </Routes>
  )
}

export default App