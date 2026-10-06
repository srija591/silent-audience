import { Routes, Route, Navigate } from 'react-router-dom'
import { getToken } from './api'
import Auth from './pages/Auth'
import Dashboard from './pages/Dashboard'
import NewAnalysis from './pages/NewAnalysis'
import Analysis from './pages/Analysis'
import Report from './pages/Report'
import QA from './pages/QA'
import Progress from './pages/Progress'
import Settings from './pages/Settings'

const Private = ({ children }) => (getToken() ? children : <Navigate to="/" replace />)

export default function App() {
  return (
    <Routes>
      <Route path="/" element={getToken() ? <Navigate to="/dashboard" replace /> : <Auth />} />
      <Route path="/dashboard" element={<Private><Dashboard /></Private>} />
      <Route path="/new" element={<Private><NewAnalysis /></Private>} />
      <Route path="/analysis/:id" element={<Private><Analysis /></Private>} />
      <Route path="/report/:id" element={<Private><Report /></Private>} />
      <Route path="/qa/:id" element={<Private><QA /></Private>} />
      <Route path="/progress" element={<Private><Progress /></Private>} />
      <Route path="/settings" element={<Private><Settings /></Private>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
