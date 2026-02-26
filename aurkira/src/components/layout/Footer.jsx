import { Link } from 'react-router-dom'
import { Heart, Mic, Globe, Shield, Brain, Mail, Phone, MapPin } from 'lucide-react'

export default function Footer() {
    return (
        <footer style={{ background: '#1a0a12', color: '#f5d0de', marginTop: 'auto' }}>
            {/* CTA Banner */}
            <div style={{ background: 'var(--gradient-primary)', padding: '48px 0' }}>
                <div className="container" style={{ textAlign: 'center' }}>
                    <h3 style={{ fontFamily: 'Playfair Display, serif', fontSize: 28, color: '#fff', marginBottom: 8 }}>
                        Ready to Transform Your Customer Experience?
                    </h3>
                    <p style={{ color: 'rgba(255,255,255,0.85)', marginBottom: 24, fontSize: 16 }}>
                        Replace IVR frustration with intelligent, empathetic AI voice support.
                    </p>
                    <Link to="/demo" className="btn btn-outline" style={{ borderColor: '#fff', color: '#fff' }}>
                        <Mic size={16} /> Try Live Demo
                    </Link>
                </div>
            </div>

            {/* Main footer */}
            <div className="container" style={{ padding: '60px 24px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', gap: 40, marginBottom: 48 }}>
                    {/* Brand */}
                    <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                            <div style={{ width: 40, height: 40, borderRadius: '50%', background: 'var(--gradient-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, fontWeight: 800, color: '#fff', fontFamily: 'Playfair Display, serif' }}>A</div>
                            <span style={{ fontFamily: 'Playfair Display, serif', fontSize: 22, color: '#fff', fontWeight: 700 }}>Aurkira</span>
                        </div>
                        <p style={{ fontSize: 14, lineHeight: 1.8, color: '#c49aab', maxWidth: 280, marginBottom: 20 }}>
                            AI-powered voice chatbot platform for real-time, human-like customer assistance.
                            Supporting 10+ Indian regional languages.
                        </p>
                    </div>

                    {/* Product */}
                    <div>
                        <h4 style={{ color: '#fff', fontWeight: 700, marginBottom: 20, fontSize: 14, textTransform: 'uppercase', letterSpacing: 1 }}>Product</h4>
                        <ul style={{ listStyle: 'none' }}>
                            {[
                                { label: 'Voice Demo', icon: Mic },
                                { label: 'Languages', icon: Globe },
                                { label: 'Sentiment AI', icon: Brain },
                                { label: 'Security', icon: Shield },
                            ].map(l => (
                                <li key={l.label} style={{ marginBottom: 10 }}>
                                    <a href="#" style={{ color: '#c49aab', fontSize: 14, textDecoration: 'none', transition: 'color var(--transition)', display: 'flex', alignItems: 'center', gap: 8 }}
                                        onMouseEnter={e => e.currentTarget.style.color = 'var(--color-primary-light)'}
                                        onMouseLeave={e => e.currentTarget.style.color = '#c49aab'}>
                                        <l.icon size={14} /> {l.label}
                                    </a>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Use Cases */}
                    <div>
                        <h4 style={{ color: '#fff', fontWeight: 700, marginBottom: 20, fontSize: 14, textTransform: 'uppercase', letterSpacing: 1 }}>Use Cases</h4>
                        <ul style={{ listStyle: 'none' }}>
                            {['Banking', 'E-Commerce', 'Healthcare', 'Telecom', 'Travel'].map(l => (
                                <li key={l} style={{ marginBottom: 10 }}>
                                    <a href="#" style={{ color: '#c49aab', fontSize: 14, textDecoration: 'none', transition: 'color var(--transition)' }}
                                        onMouseEnter={e => e.currentTarget.style.color = 'var(--color-primary-light)'}
                                        onMouseLeave={e => e.currentTarget.style.color = '#c49aab'}>{l}</a>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Contact */}
                    <div>
                        <h4 style={{ color: '#fff', fontWeight: 700, marginBottom: 20, fontSize: 14, textTransform: 'uppercase', letterSpacing: 1 }}>Contact</h4>
                        <ul style={{ listStyle: 'none' }}>
                            {[
                                { Icon: Mail, text: 'hello@aurkira.ai' },
                                { Icon: Phone, text: '+91 (800) 287-4527' },
                                { Icon: MapPin, text: 'Pune, Maharashtra, India' },
                            ].map(({ Icon, text }) => (
                                <li key={text} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14, color: '#c49aab', fontSize: 14 }}>
                                    <Icon size={14} style={{ color: 'var(--color-primary-light)', flexShrink: 0 }} />
                                    {text}
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                {/* Bottom */}
                <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 24, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <p style={{ color: '#9e6a80', fontSize: 13 }}>
                        © 2026 Aurkira · Built by Team InvoCreatz · Made with <Heart size={12} style={{ display: 'inline', color: 'var(--color-primary)', verticalAlign: 'middle' }} /> in India
                    </p>
                    <div style={{ display: 'flex', gap: 20 }}>
                        {['Privacy Policy', 'Terms of Service'].map(l => (
                            <a key={l} href="#" style={{ color: '#9e6a80', fontSize: 12, textDecoration: 'none' }}>{l}</a>
                        ))}
                    </div>
                </div>
            </div>
        </footer>
    )
}
