import { Navigate, Route, Routes } from 'react-router-dom'
import Dashboard from './views/Dashboard'
import HabitConfig from './views/HabitConfig'
import FocusView from './views/FocusView'
import Stats from './views/Stats'
import Settings from './views/Settings'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/new" element={<HabitConfig />} />
      <Route path="/habit/:id" element={<FocusView />} />
      <Route path="/habit/:id/edit" element={<HabitConfig />} />
      <Route path="/stats" element={<Stats />} />
      <Route path="/settings" element={<Settings />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
