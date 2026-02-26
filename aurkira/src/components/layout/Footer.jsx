import { Link } from 'react-router-dom'
import { Heart, Instagram, Twitter, Facebook, Youtube, Mail, Phone, MapPin } from 'lucide-react'

export default function Footer() {
    return (
        <footer style={{ background: '#1a0a12', color: '#f5d0de', marginTop: 'auto' }}>
            {/* Newsletter */}
            <div style={{ background: 'var(--gradient-primary)', padding: '48px 0' }}>
                <div className="container" style={{ textAlign: 'center' }}>
                    <h3 style={{ fontFamily: 'Playfair Display, serif', fontSize: 28, color: '#fff', marginBottom: 8 }}>
                        Stay in the loop
                    </h3>
                    <p style={{ color: 'rgba(255,255,255,0.85)', marginBottom: 24, fontSize: 16 }}>
                        Get the latest trends, exclusive deals, and style tips delivered to your inbox.
                    </p>
                    <form style={{ display: 'flex', gap: 12, maxWidth: 440, margin: '0 auto' }} onSubmit={e => e.preventDefault()}>
                        <input
                            type="email"
                            placeholder="Enter your email"
                            className="input"
                            style={{ flex: 1, borderColor: 'rgba(255,255,255,0.3)', background: 'rgba(255,255,255,0.15)', color: '#fff' }}
                        />
                        <button className="btn btn-outline" style={{ borderColor: '#fff', color: '#fff', flexShrink: 0 }}>
                            Subscribe
                        </button>
                    </form>
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
                        <p style={{ fontSize: 14, lineHeight: 1.8, color: '#c49aab', maxWidth: 260, marginBottom: 20 }}>
                            Your destination for premium fashion. Discover curated collections that blend style with sophistication.
                        </p>
                        <div style={{ display: 'flex', gap: 12 }}>
                            {[Instagram, Twitter, Facebook, Youtube].map((Icon, i) => (
                                <a key={i} href="#" style={{ width: 36, height: 36, borderRadius: '50%', background: 'rgba(233,30,140,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-primary-light)', transition: 'all var(--transition)', textDecoration: 'none' }}
                                    onMouseEnter={e => { e.currentTarget.style.background = 'var(--color-primary)'; e.currentTarget.style.color = '#fff' }}
                                    onMouseLeave={e => { e.currentTarget.style.background = 'rgba(233,30,140,0.15)'; e.currentTarget.style.color = 'var(--color-primary-light)' }}>
                                    <Icon size={16} />
                                </a>
                            ))}
                        </div>
                    </div>

                    {/* Shop */}
                    <div>
                        <h4 style={{ color: '#fff', fontWeight: 700, marginBottom: 20, fontSize: 14, textTransform: 'uppercase', letterSpacing: 1 }}>Shop</h4>
                        <ul style={{ listStyle: 'none' }}>
                            {["Women's Collection", "Men's Collection", "New Arrivals", "Sale", "Trending"].map(l => (
                                <li key={l} style={{ marginBottom: 10 }}>
                                    <a href="#" style={{ color: '#c49aab', fontSize: 14, textDecoration: 'none', transition: 'color var(--transition)' }}
                                        onMouseEnter={e => e.currentTarget.style.color = 'var(--color-primary-light)'}
                                        onMouseLeave={e => e.currentTarget.style.color = '#c49aab'}>{l}</a>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Help */}
                    <div>
                        <h4 style={{ color: '#fff', fontWeight: 700, marginBottom: 20, fontSize: 14, textTransform: 'uppercase', letterSpacing: 1 }}>Help</h4>
                        <ul style={{ listStyle: 'none' }}>
                            {['My Account', 'Orders & Returns', 'Shipping Info', 'Size Guide', 'Contact Us'].map(l => (
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
                                { Icon: Mail, text: 'hello@aurkira.com' },
                                { Icon: Phone, text: '+1 (800) 287-4527' },
                                { Icon: MapPin, text: 'New York, NY 10001' },
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
                        © 2025 Aurkira. Made with <Heart size={12} style={{ display: 'inline', color: 'var(--color-primary)', verticalAlign: 'middle' }} /> All rights reserved.
                    </p>
                    <div style={{ display: 'flex', gap: 20 }}>
                        {['Privacy Policy', 'Terms of Service', 'Cookies'].map(l => (
                            <a key={l} href="#" style={{ color: '#9e6a80', fontSize: 12, textDecoration: 'none' }}>{l}</a>
                        ))}
                    </div>
                </div>
            </div>
        </footer>
    )
}
