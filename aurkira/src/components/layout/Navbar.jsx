import { useState, useRef, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { Search, Heart, ShoppingBag, User, ChevronDown, Menu, X } from 'lucide-react'
import { useCartStore } from '../../store/cartStore'
import { useFavoritesStore } from '../../store/favoritesStore'
import productsData from '../../data/products.json'

const womenMenu = {
    Clothing: ['Tops', 'Dresses', 'Jeans & Jeggings', 'Skirts', 'Trousers & Pants', 'Sweaters & Cardigans', 'T-Shirts', 'Jackets & Coats', 'Lingerie & Sleepwear'],
    Footwear: ['Heels', 'Sandals', 'Sneakers & Athletic Shoes', 'Boots', 'Flats'],
    Accessories: ['Watches', 'Handbags', 'Jewellery', 'Sunglasses', 'Hats & Caps', 'Belts', 'Scarves & Wraps'],
}

const menMenu = {
    Clothing: ['T-Shirts', 'Shirts', 'Jeans', 'Trousers & Chinos', 'Sweaters & Cardigans', 'Jackets & Coats', 'Suits & Blazers', 'Shorts'],
    Footwear: ['Formal Shoes', 'Sneakers & Athletic Shoes', 'Boots', 'Sandals & Floaters', 'Loafers'],
    Accessories: ['Watches', 'Sunglasses', 'Belts', 'Wallets', 'Hats & Caps', 'Ties & Cufflinks'],
}

export default function Navbar() {
    const [activeDropdown, setActiveDropdown] = useState(null)
    const [searchOpen, setSearchOpen] = useState(false)
    const [searchQuery, setSearchQuery] = useState('')
    const [searchResults, setSearchResults] = useState([])
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
    const searchRef = useRef(null)
    const navigate = useNavigate()
    const location = useLocation()

    const cartCount = useCartStore(s => s.getCount())
    const openCart = useCartStore(s => s.openCart)
    const favCount = useFavoritesStore(s => s.items.length)

    // Close dropdown on route change
    useEffect(() => {
        setActiveDropdown(null)
        setMobileMenuOpen(false)
    }, [location.pathname])

    // Search logic
    useEffect(() => {
        if (searchQuery.trim().length < 2) { setSearchResults([]); return }
        const q = searchQuery.toLowerCase()
        const results = productsData.products.filter(p =>
            p.name.toLowerCase().includes(q) ||
            p.searchTerms?.some(t => t.includes(q))
        ).slice(0, 5)
        setSearchResults(results)
    }, [searchQuery])

    const handleSearchSubmit = (e) => {
        e.preventDefault()
        if (searchQuery.trim()) {
            setSearchOpen(false)
            setSearchQuery('')
            navigate(`/shop/women?search=${encodeURIComponent(searchQuery)}`)
        }
    }

    return (
        <>
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
                        ✨ Free shipping on orders over $100 · Use code <strong>AURKIRA20</strong> for 20% off
                    </p>
                </div>

                {/* Main nav */}
                <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 24px', height: '68px', gap: '16px' }}>
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

                    {/* Search bar — desktop */}
                    <div style={{ flex: 1, maxWidth: 480, position: 'relative' }} className="desktop-search">
                        <form onSubmit={handleSearchSubmit}>
                            <div style={{ position: 'relative' }}>
                                <Search size={16} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-light)' }} />
                                <input
                                    ref={searchRef}
                                    value={searchQuery}
                                    onChange={e => setSearchQuery(e.target.value)}
                                    placeholder="Search products..."
                                    className="input"
                                    style={{ paddingLeft: 40, paddingRight: 16, fontSize: '14px', height: 42 }}
                                />
                            </div>
                        </form>
                        {/* Search results dropdown */}
                        {searchResults.length > 0 && (
                            <div style={{
                                position: 'absolute', top: '110%', left: 0, right: 0,
                                background: '#fff', borderRadius: 'var(--radius-md)',
                                boxShadow: 'var(--shadow-lg)', border: '1px solid var(--color-border-light)',
                                zIndex: 400, overflow: 'hidden',
                            }}>
                                {searchResults.map(p => (
                                    <Link
                                        key={p.id}
                                        to={`/product/${p.id}`}
                                        onClick={() => { setSearchQuery(''); setSearchResults([]) }}
                                        style={{
                                            display: 'flex', alignItems: 'center', gap: 12,
                                            padding: '10px 16px', textDecoration: 'none',
                                            borderBottom: '1px solid var(--color-border-light)',
                                            transition: 'background var(--transition)',
                                        }}
                                        onMouseEnter={e => e.currentTarget.style.background = 'var(--color-bg-soft)'}
                                        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                                    >
                                        <img src={p.image} alt={p.name} style={{ width: 36, height: 36, objectFit: 'cover', borderRadius: 6 }} />
                                        <div>
                                            <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)' }}>{p.name}</p>
                                            <p style={{ fontSize: 12, color: 'var(--color-primary)', fontWeight: 700 }}>${p.price}</p>
                                        </div>
                                    </Link>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Right icons */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexShrink: 0 }}>
                        <button className="btn-icon" onClick={() => setMobileMenuOpen(!mobileMenuOpen)} style={{ display: 'none' }} id="mobile-menu-btn">
                            {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
                        </button>
                        <Link to="/favorites" className="btn-icon" style={{ position: 'relative', textDecoration: 'none' }}>
                            <Heart size={20} />
                            {favCount > 0 && (
                                <span style={{
                                    position: 'absolute', top: 0, right: 0, width: 18, height: 18,
                                    background: 'var(--gradient-primary)', color: '#fff', borderRadius: '50%',
                                    fontSize: 10, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center',
                                }}>{favCount}</span>
                            )}
                        </Link>
                        <button className="btn-icon" onClick={openCart} style={{ position: 'relative' }}>
                            <ShoppingBag size={20} />
                            {cartCount > 0 && (
                                <span style={{
                                    position: 'absolute', top: 0, right: 0, width: 18, height: 18,
                                    background: 'var(--gradient-primary)', color: '#fff', borderRadius: '50%',
                                    fontSize: 10, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center',
                                }}>{cartCount}</span>
                            )}
                        </button>
                        <Link to="/login" className="btn-icon" style={{ textDecoration: 'none' }}>
                            <User size={20} />
                        </Link>
                    </div>
                </div>

                {/* Nav links row */}
                <nav style={{ borderTop: '1px solid var(--color-border-light)', background: '#fff' }}>
                    <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 44 }}>
                        {/* Home */}
                        <Link to="/" style={{
                            textDecoration: 'none', padding: '0 20px', height: 44, display: 'flex', alignItems: 'center',
                            fontSize: '14px', fontWeight: 500, color: location.pathname === '/' ? 'var(--color-primary)' : 'var(--color-text)',
                            borderBottom: location.pathname === '/' ? '2px solid var(--color-primary)' : '2px solid transparent',
                            transition: 'all var(--transition)',
                        }}>Home</Link>

                        {/* Women dropdown */}
                        <div
                            style={{ position: 'relative' }}
                            onMouseEnter={() => setActiveDropdown('women')}
                            onMouseLeave={() => setActiveDropdown(null)}
                        >
                            <Link to="/shop/women" style={{
                                textDecoration: 'none', padding: '0 20px', height: 44, display: 'flex', alignItems: 'center', gap: 4,
                                fontSize: '14px', fontWeight: 500,
                                color: location.pathname.includes('women') ? 'var(--color-primary)' : 'var(--color-text)',
                                borderBottom: location.pathname.includes('women') ? '2px solid var(--color-primary)' : '2px solid transparent',
                                transition: 'all var(--transition)',
                            }}>
                                Women <ChevronDown size={14} style={{ transition: 'transform 0.2s', transform: activeDropdown === 'women' ? 'rotate(180deg)' : 'rotate(0)' }} />
                            </Link>
                            {/* Women mega menu */}
                            <MegaMenu data={womenMenu} isOpen={activeDropdown === 'women'} gender="women" />
                        </div>

                        {/* Men dropdown */}
                        <div
                            style={{ position: 'relative' }}
                            onMouseEnter={() => setActiveDropdown('men')}
                            onMouseLeave={() => setActiveDropdown(null)}
                        >
                            <Link to="/shop/men" style={{
                                textDecoration: 'none', padding: '0 20px', height: 44, display: 'flex', alignItems: 'center', gap: 4,
                                fontSize: '14px', fontWeight: 500,
                                color: location.pathname.includes('men') && !location.pathname.includes('women') ? 'var(--color-primary)' : 'var(--color-text)',
                                borderBottom: location.pathname.includes('men') && !location.pathname.includes('women') ? '2px solid var(--color-primary)' : '2px solid transparent',
                                transition: 'all var(--transition)',
                            }}>
                                Men <ChevronDown size={14} style={{ transition: 'transform 0.2s', transform: activeDropdown === 'men' ? 'rotate(180deg)' : 'rotate(0)' }} />
                            </Link>
                            <MegaMenu data={menMenu} isOpen={activeDropdown === 'men'} gender="men" />
                        </div>

                        <Link to="/" style={{ textDecoration: 'none', padding: '0 20px', height: 44, display: 'flex', alignItems: 'center', fontSize: '14px', fontWeight: 500, color: 'var(--color-text)', borderBottom: '2px solid transparent' }}>About</Link>
                        <Link to="/" style={{ textDecoration: 'none', padding: '0 20px', height: 44, display: 'flex', alignItems: 'center', fontSize: '14px', fontWeight: 500, color: 'var(--color-text)', borderBottom: '2px solid transparent' }}>Contact</Link>
                    </div>
                </nav>
            </header>
        </>
    )
}

function MegaMenu({ data, isOpen, gender }) {
    const navigate = useNavigate()
    const categoryColors = { Clothing: 'var(--color-primary)', Footwear: '#0ea5e9', Accessories: '#a855f7' }

    return (
        <div className={`nav-dropdown ${isOpen ? 'open' : ''}`} style={{ transform: 'translateX(-30%)', minWidth: 680 }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 32 }}>
                {Object.entries(data).map(([category, items]) => (
                    <div key={category}>
                        <h4 style={{ fontSize: 13, fontWeight: 700, color: categoryColors[category] || 'var(--color-primary)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                            {category}
                        </h4>
                        <ul style={{ listStyle: 'none' }}>
                            {items.map(item => (
                                <li key={item}>
                                    <button
                                        onClick={() => navigate(`/shop/${gender}?category=${encodeURIComponent(item.toLowerCase())}`)}
                                        style={{
                                            background: 'none', border: 'none', cursor: 'pointer',
                                            padding: '5px 0', fontSize: 13, color: 'var(--color-text-secondary)',
                                            display: 'block', transition: 'color var(--transition)', textAlign: 'left',
                                            fontFamily: 'Inter, sans-serif',
                                        }}
                                        onMouseEnter={e => e.currentTarget.style.color = 'var(--color-primary)'}
                                        onMouseLeave={e => e.currentTarget.style.color = 'var(--color-text-secondary)'}
                                    >{item}</button>
                                </li>
                            ))}
                        </ul>
                    </div>
                ))}
            </div>
        </div>
    )
}
