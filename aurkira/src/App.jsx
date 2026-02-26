import { Routes, Route, useLocation } from 'react-router-dom'
import Navbar from './components/layout/Navbar'
import Footer from './components/layout/Footer'
import Landing from './pages/Landing'
import VoiceDemo from './pages/VoiceDemo'

export default function App() {
  const location = useLocation()
  const isDemo = location.pathname === '/demo'

  if (isDemo) {
    return <VoiceDemo />
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />
      <main style={{ flex: 1 }}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/demo" element={<VoiceDemo />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}
