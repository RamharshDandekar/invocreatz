import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Menu, X, Mic } from 'lucide-react'

export default function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const location = useLocation()

  const navLinks = [
    { label: 'Home', path: '/' },
    { label: 'Features', path: '/#features' },
    { label: 'Demo', path: '/demo' },
  ]

  return (
    <header style={{
      position: 'sticky', top: 0, zIndex: 300,
      background: 'rgba(255,255,255,0.95)',
      backdropFilter: 'blur(16px)',
      borderBottom: '1px solid var(--color-border-light)',
      boxShadow: '0 1px 12px rgba(233,30,140,0.06)',
    }}>
      {/* Top bar */}
      <div style={{ background: 'var(--gradient-primary)', padding: '6px 0', textAlign: 'center' }}>
        <p style={{ color: '#fff', fontSize: '12px', fontWeight: 500, letterSpacing: '0.5px' }}>
          🎤 AI Voice Chatbot — Replace Your IVR System Today · Supports 10+ Indian Languages
        </p>
      </div>

      {/* Main nav */}
      <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 24px', height: '68px' }}>
        {/* Logo */}
        <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
          <div style={{
            width: 42, height: 42, borderRadius: '50%',
            background: 'var(--gradient-primary)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '18px', fontWeight: 800, color: '#fff',
            fontFamily: 'Playfair Display, serif',
            boxShadow: 'var(--shadow-md)',
          }}>A</div>
          <span style={{ fontFamily: 'Playfair Display, serif', fontSize: '22px', fontWeight: 700, color: 'var(--color-text)', letterSpacing: '-0.5px' }}>
            Aurkira
          </span>
        </Link>

        {/* Nav links */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {navLinks.map(link => (
            <Link
              key={link.path}
              to={link.path}
              style={{
                textDecoration: 'none',
                padding: '8px 20px',
                fontSize: '14px',
                fontWeight: 500,
                color: location.pathname === link.path ? 'var(--color-primary)' : 'var(--color-text)',
                borderRadius: 'var(--radius-full)',
                transition: 'all var(--transition)',
              }}
              onMouseEnter={e => { e.currentTarget.style.background = 'var(--color-bg-pink)'; e.currentTarget.style.color = 'var(--color-primary)' }}
              onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = location.pathname === link.path ? 'var(--color-primary)' : 'var(--color-text)' }}
            >
              {link.label}
            </Link>
          ))}

          <Link
            to="/demo"
            className="btn btn-primary btn-sm"
            style={{ marginLeft: 8, display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <Mic size={14} /> Try Voice Demo
          </Link>
        </nav>
      </div>
    </header>
  )
}
