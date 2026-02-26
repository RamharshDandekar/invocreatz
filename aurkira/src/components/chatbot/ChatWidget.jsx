import { useState, useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import { MessageSquare, X, Send, Mic, MicOff, Image, Globe, ChevronDown, Upload } from 'lucide-react'
import { GoogleGenerativeAI } from '@google/generative-ai'
import productsData from '../../data/products.json'
import { useCartStore } from '../../store/cartStore'
import { useFavoritesStore } from '../../store/favoritesStore'

const API_KEY = import.meta.env.VITE_GEMINI_API_KEY

const LANGUAGES = [
    { code: 'en', name: 'English', flag: '🇺🇸', speechLang: 'en-US' },
    { code: 'hi', name: 'हिंदी', flag: '🇮🇳', speechLang: 'hi-IN' },
    { code: 'es', name: 'Español', flag: '🇪🇸', speechLang: 'es-ES' },
    { code: 'fr', name: 'Français', flag: '🇫🇷', speechLang: 'fr-FR' },
    { code: 'de', name: 'Deutsch', flag: '🇩🇪', speechLang: 'de-DE' },
    { code: 'ja', name: '日本語', flag: '🇯🇵', speechLang: 'ja-JP' },
]

export default function ChatWidget() {
    const [isOpen, setIsOpen] = useState(false)
    const [messages, setMessages] = useState([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [showNotification, setShowNotification] = useState(false)
    const [notifMsg, setNotifMsg] = useState('')
    const [hasShownInitial, setHasShownInitial] = useState(false)
    const [selectedLang, setSelectedLang] = useState(LANGUAGES[0])
    const [showLangMenu, setShowLangMenu] = useState(false)
    const [isVoiceMode, setIsVoiceMode] = useState(false)
    const [isListening, setIsListening] = useState(false)
    const [isSpeaking, setIsSpeaking] = useState(false)
    const [selectedImage, setSelectedImage] = useState(null)
    const messagesEndRef = useRef(null)
    const recognitionRef = useRef(null)
    const fileInputRef = useRef(null)
    const location = useLocation()
    const cartItems = useCartStore(s => s.items)
    const favItems = useFavoritesStore(s => s.items)

    useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

    // Initial greeting after 3s
    useEffect(() => {
        if (hasShownInitial) return
        const timer = setTimeout(async () => {
            const msg = await getInitialMessage(location.pathname)
            setNotifMsg(msg)
            setShowNotification(true)
            setHasShownInitial(true)
            setTimeout(() => setShowNotification(false), 5000)
        }, 3000)
        return () => clearTimeout(timer)
    }, [location.pathname, hasShownInitial])

    // Cart event
    useEffect(() => {
        const handler = async (e) => {
            if (!API_KEY) return
            const { product } = e.detail
            const suggestion = await getSuggestion(product, 'cart')
            addBotMessage(suggestion)
            setNotifMsg(suggestion)
            setShowNotification(true)
            setTimeout(() => setShowNotification(false), 5000)
        }
        const favHandler = async (e) => {
            if (!API_KEY) return
            const { product } = e.detail
            const suggestion = await getSuggestion(product, 'favorites')
            addBotMessage(suggestion)
        }
        window.addEventListener('itemAddedToCart', handler)
        window.addEventListener('itemAddedToFavorites', favHandler)
        return () => {
            window.removeEventListener('itemAddedToCart', handler)
            window.removeEventListener('itemAddedToFavorites', favHandler)
        }
    }, [selectedLang])

    const addBotMessage = (text) => {
        setMessages(prev => [...prev, { id: Date.now(), text, isBot: true, ts: new Date() }])
    }

    const getInitialMessage = async (pathname) => {
        const today = new Date()
        const m = today.getMonth() + 1, d = today.getDate()
        let occasion = ''
        if (m === 2 && d === 14) occasion = "Valentine's Day"
        else if (m === 12 && d >= 20) occasion = 'Christmas season'

        if (pathname === '/') return "Hi! I'm your Aurkira fashion assistant 💕 What are you looking for today? I can help you discover amazing products with the best deals!"
        if (pathname.includes('women')) return "Hi! Browsing our women's collection? I can help you find the perfect outfit or suggest deals! 🌸"
        if (pathname.includes('men')) return "Welcome! Looking for something in our men's section? I'm here to help you style up! 👔"
        if (pathname.includes('product')) return "I see you're checking out a product! I can compare it with similar items or suggest what pairs well with it."
        if (pathname.includes('favorites')) return "Looking at your saved items? I can help you decide between them or suggest additions! ❤️"
        return "Hello! I'm your Aurkira assistant. How can I help you today? 💕"
    }

    const getSuggestion = async (product, action) => {
        if (!API_KEY) return `Great choice! Check out more ${product.category} items!`
        try {
            const genAI = new GoogleGenerativeAI(API_KEY)
            const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' })
            const related = productsData.products.filter(p => p.id !== product.id && p.category === product.category).slice(0, 4)
            const prompt = `You are a fashion assistant for Aurkira. Customer just ${action === 'cart' ? 'added to cart' : 'saved to favorites'}: "${product.name}" ($${product.price}). Suggest 2 complementary items from: ${JSON.stringify(related)}. Keep it under 80 words, be enthusiastic!`
            const result = await model.generateContent(prompt)
            return result.response.text()
        } catch { return `Excellent choice! This pairs beautifully with other items in our collection!` }
    }

    const buildSystemPrompt = () => {
        const today = new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
        const m = new Date().getMonth() + 1, d = new Date().getDate()
        let occasion = ''
        if (m === 2 && d === 14) occasion = "Valentine's Day"
        else if (m === 12 && d >= 20) occasion = 'Christmas season'

        return `You are a professional fashion assistant for Aurkira, a premium e-commerce website. Respond in ${selectedLang.name}.

CURRENT CONTEXT:
- Date: ${today}
- Special occasion: ${occasion || 'None'}
- Current page: ${location.pathname}
- Items in cart: ${cartItems.length} (${cartItems.map(i => i.name).join(', ')})
- Favorite items: ${favItems.length}

COMPLETE PRODUCT INVENTORY:
${JSON.stringify(productsData.products.slice(0, 20))}

WEBSITE URLs:
- Home: /
- Women's Shop: /shop/women
- Men's Shop: /shop/men
- Product Detail: /product/:id
- Favorites: /favorites

GUIDELINES:
1. Highlight products on sale (originalPrice > price)
2. Be enthusiastic but professional
3. Suggest specific products with prices
4. Keep responses under 150 words
5. ALWAYS respond in ${selectedLang.name}
6. For voice mode, avoid bullet points and markdown`
    }

    const sendMessage = async (text, imageBase64 = null) => {
        if (!text.trim() && !imageBase64) return
        const userMsg = { id: Date.now(), text: text || 'What do you think about this?', isBot: false, image: imageBase64 ? `data:image/jpeg;base64,${imageBase64}` : null, ts: new Date() }
        setMessages(prev => [...prev, userMsg])
        setInput('')
        setSelectedImage(null)
        setLoading(true)

        if (!API_KEY) {
            setTimeout(() => {
                addBotMessage("I'm having trouble connecting right now. Please add your VITE_GEMINI_API_KEY to your .env file!")
                setLoading(false)
            }, 1000)
            return
        }

        try {
            const genAI = new GoogleGenerativeAI(API_KEY)
            const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' })
            const systemPrompt = buildSystemPrompt()
            const parts = [`${systemPrompt}\n\nUser message: "${text}"`]
            if (imageBase64) parts.push({ inlineData: { data: imageBase64, mimeType: 'image/jpeg' } })
            const result = await model.generateContent(parts)
            const response = result.response.text()
            addBotMessage(response)
            if (isVoiceMode) speakText(response)
        } catch (err) {
            addBotMessage("I'm having trouble responding right now. Please try again!")
        } finally {
            setLoading(false)
        }
    }

    const speakText = (text) => {
        if (!('speechSynthesis' in window)) return
        window.speechSynthesis.cancel()
        const utt = new SpeechSynthesisUtterance(text.replace(/[*_#]/g, ''))
        utt.lang = selectedLang.speechLang
        utt.rate = 0.9
        utt.onstart = () => setIsSpeaking(true)
        utt.onend = () => { setIsSpeaking(false); if (isVoiceMode) startListening() }
        window.speechSynthesis.speak(utt)
    }

    const startListening = () => {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition
        if (!SR) return
        const rec = new SR()
        rec.lang = selectedLang.speechLang
        rec.continuous = false
        rec.interimResults = false
        rec.onstart = () => setIsListening(true)
        rec.onend = () => setIsListening(false)
        rec.onresult = (e) => {
            const t = e.results[0][0].transcript
            if (t) sendMessage(t)
        }
        rec.onerror = () => setIsListening(false)
        recognitionRef.current = rec
        rec.start()
    }

    const stopListening = () => { recognitionRef.current?.stop() }

    const handleImageUpload = (e) => {
        const file = e.target.files?.[0]
        if (!file) return
        const reader = new FileReader()
        reader.onload = (ev) => setSelectedImage(ev.target.result)
        reader.readAsDataURL(file)
    }

    const handleSend = () => {
        if (selectedImage) {
            const base64 = selectedImage.split(',')[1]
            sendMessage(input || 'What fashion items do you see? Find similar in our store!', base64)
        } else {
            sendMessage(input)
        }
    }

    const handleNotifClick = () => {
        setShowNotification(false)
        setIsOpen(true)
        if (notifMsg) addBotMessage(notifMsg)
    }

    return (
        <>
            {/* Notification popup */}
            {showNotification && !isOpen && (
                <div
                    onClick={handleNotifClick}
                    className="animate-slideInRight"
                    style={{
                        position: 'fixed', bottom: 90, right: 24, zIndex: 998,
                        background: '#fff', border: '1px solid var(--color-border-light)',
                        borderRadius: 'var(--radius-lg)', padding: '14px 18px',
                        maxWidth: 280, cursor: 'pointer', boxShadow: 'var(--shadow-xl)',
                    }}
                >
                    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                        <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'var(--gradient-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                            <MessageSquare size={16} color="#fff" />
                        </div>
                        <div>
                            <p style={{ fontWeight: 700, fontSize: 13, color: 'var(--color-text)', marginBottom: 4 }}>Aurkira Assistant 💕</p>
                            <p style={{ fontSize: 12, color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>{notifMsg.substring(0, 80)}...</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Floating button */}
            <button
                onClick={() => { setIsOpen(!isOpen); setShowNotification(false) }}
                style={{
                    position: 'fixed', bottom: 24, right: 24, zIndex: 999,
                    width: 56, height: 56, borderRadius: '50%',
                    background: 'var(--gradient-primary)',
                    border: 'none', cursor: 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    boxShadow: 'var(--shadow-xl)',
                    transition: 'all var(--transition)',
                }}
                onMouseEnter={e => { e.currentTarget.style.transform = 'scale(1.1)'; e.currentTarget.style.boxShadow = '0 8px 32px rgba(233,30,140,0.4)' }}
                onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)'; e.currentTarget.style.boxShadow = 'var(--shadow-xl)' }}
            >
                {isOpen ? <X size={22} color="#fff" /> : <MessageSquare size={22} color="#fff" />}
                {/* Pulse ring */}
                {!isOpen && (
                    <span style={{
                        position: 'absolute', inset: 0, borderRadius: '50%',
                        border: '2px solid var(--color-primary)',
                        animation: 'pulse-ring 2s ease-out infinite',
                    }} />
                )}
            </button>

            {/* Chat window */}
            {isOpen && (
                <div
                    className="animate-slideInRight"
                    style={{
                        position: 'fixed', bottom: 92, right: 24, zIndex: 998,
                        width: 360, height: 520,
                        background: '#fff', borderRadius: 'var(--radius-xl)',
                        boxShadow: 'var(--shadow-xl)',
                        border: '1px solid var(--color-border-light)',
                        display: 'flex', flexDirection: 'column', overflow: 'hidden',
                    }}
                >
                    {/* Header */}
                    <div style={{ background: 'var(--gradient-primary)', padding: '14px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'rgba(255,255,255,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <MessageSquare size={18} color="#fff" />
                            </div>
                            <div>
                                <p style={{ color: '#fff', fontWeight: 700, fontSize: 14 }}>Aurkira Assistant</p>
                                <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: 11 }}>{isListening ? '🎤 Listening...' : isSpeaking ? '🔊 Speaking...' : '● Online'}</p>
                            </div>
                        </div>
                        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                            {/* Language selector */}
                            <div style={{ position: 'relative' }}>
                                <button
                                    onClick={() => setShowLangMenu(!showLangMenu)}
                                    style={{ background: 'rgba(255,255,255,0.2)', border: 'none', borderRadius: 20, padding: '4px 10px', color: '#fff', cursor: 'pointer', fontSize: 12, display: 'flex', alignItems: 'center', gap: 4 }}
                                >
                                    {selectedLang.flag} <ChevronDown size={10} />
                                </button>
                                {showLangMenu && (
                                    <div style={{ position: 'absolute', top: '120%', right: 0, background: '#fff', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-lg)', overflow: 'hidden', minWidth: 140, zIndex: 10 }}>
                                        {LANGUAGES.map(lang => (
                                            <button
                                                key={lang.code}
                                                onClick={() => { setSelectedLang(lang); setShowLangMenu(false) }}
                                                style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%', padding: '8px 14px', border: 'none', background: selectedLang.code === lang.code ? 'var(--color-bg-pink)' : '#fff', cursor: 'pointer', fontSize: 13, color: 'var(--color-text)', textAlign: 'left', fontFamily: 'Inter, sans-serif' }}
                                            >
                                                <span>{lang.flag}</span> {lang.name}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                            <button onClick={() => setIsVoiceMode(!isVoiceMode)} style={{ background: isVoiceMode ? 'rgba(255,255,255,0.3)' : 'rgba(255,255,255,0.15)', border: 'none', borderRadius: '50%', width: 30, height: 30, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
                                {isVoiceMode ? <Mic size={14} /> : <MicOff size={14} />}
                            </button>
                            <button onClick={() => setIsOpen(false)} style={{ background: 'rgba(255,255,255,0.15)', border: 'none', borderRadius: '50%', width: 30, height: 30, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
                                <X size={14} />
                            </button>
                        </div>
                    </div>

                    {/* Messages */}
                    <div style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
                        {messages.length === 0 && (
                            <div style={{ textAlign: 'center', padding: '20px 10px' }}>
                                <div style={{ fontSize: 32, marginBottom: 8 }}>💕</div>
                                <p style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>Your personal fashion assistant. Ask me anything!</p>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, justifyContent: 'center', marginTop: 16 }}>
                                    {['Show me dresses on sale', 'What\'s trending?', 'Help me find a gift'].map(q => (
                                        <button key={q} onClick={() => sendMessage(q)} style={{ fontSize: 11, padding: '6px 12px', borderRadius: 20, border: '1px solid var(--color-border)', background: '#fff', cursor: 'pointer', color: 'var(--color-primary)', fontFamily: 'Inter, sans-serif', transition: 'all var(--transition)' }}
                                            onMouseEnter={e => { e.currentTarget.style.background = 'var(--color-bg-pink)' }}
                                            onMouseLeave={e => { e.currentTarget.style.background = '#fff' }}>
                                            {q}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}
                        {messages.map(msg => (
                            <div key={msg.id} style={{ display: 'flex', flexDirection: 'column', alignItems: msg.isBot ? 'flex-start' : 'flex-end' }}>
                                {msg.image && <img src={msg.image} alt="upload" style={{ maxWidth: 120, borderRadius: 8, marginBottom: 6, alignSelf: msg.isBot ? 'flex-start' : 'flex-end' }} />}
                                <div className={msg.isBot ? 'chat-bubble-bot' : 'chat-bubble-user'} style={{ whiteSpace: 'pre-wrap' }}>
                                    {msg.text}
                                </div>
                                <span style={{ fontSize: 10, color: 'var(--color-text-light)', marginTop: 2 }}>
                                    {msg.ts?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </span>
                            </div>
                        ))}
                        {loading && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '10px 16px', background: 'var(--color-bg-soft)', borderRadius: '18px 18px 18px 4px', alignSelf: 'flex-start' }}>
                                <div className="typing-dot" />
                                <div className="typing-dot" />
                                <div className="typing-dot" />
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Image preview */}
                    {selectedImage && (
                        <div style={{ padding: '8px 16px', borderTop: '1px solid var(--color-border-light)', display: 'flex', alignItems: 'center', gap: 8 }}>
                            <img src={selectedImage} alt="preview" style={{ height: 48, borderRadius: 6, objectFit: 'cover' }} />
                            <p style={{ fontSize: 12, color: 'var(--color-text-muted)', flex: 1 }}>Image selected</p>
                            <button onClick={() => setSelectedImage(null)} className="btn-icon" style={{ width: 24, height: 24 }}><X size={14} /></button>
                        </div>
                    )}

                    {/* Input */}
                    <div style={{ padding: '12px 16px', borderTop: '1px solid var(--color-border-light)', display: 'flex', gap: 8, alignItems: 'center' }}>
                        <button onClick={() => fileInputRef.current?.click()} className="btn-icon" style={{ flexShrink: 0, color: 'var(--color-text-muted)' }}>
                            <Image size={18} />
                        </button>
                        <input
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
                            placeholder={selectedImage ? 'Ask about this image...' : `Message in ${selectedLang.name}...`}
                            style={{ flex: 1, padding: '9px 14px', border: '1.5px solid var(--color-border)', borderRadius: 'var(--radius-full)', fontSize: 13, outline: 'none', fontFamily: 'Inter, sans-serif', transition: 'border-color var(--transition)' }}
                            onFocus={e => e.target.style.borderColor = 'var(--color-primary)'}
                            onBlur={e => e.target.style.borderColor = 'var(--color-border)'}
                        />
                        {isVoiceMode && (
                            <button
                                onClick={isListening ? stopListening : startListening}
                                style={{
                                    width: 36, height: 36, borderRadius: '50%', flexShrink: 0,
                                    background: isListening ? 'var(--gradient-primary)' : 'var(--color-bg-pink)',
                                    border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    color: isListening ? '#fff' : 'var(--color-primary)',
                                    animation: isListening ? 'bounce-gentle 1s infinite' : 'none',
                                }}
                            >
                                {isListening ? <Mic size={16} /> : <MicOff size={16} />}
                            </button>
                        )}
                        <button
                            onClick={handleSend}
                            disabled={loading || (!input.trim() && !selectedImage)}
                            style={{
                                width: 36, height: 36, borderRadius: '50%', flexShrink: 0,
                                background: (loading || (!input.trim() && !selectedImage)) ? 'var(--color-bg-pink)' : 'var(--gradient-primary)',
                                border: 'none', cursor: (loading || (!input.trim() && !selectedImage)) ? 'not-allowed' : 'pointer',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                transition: 'all var(--transition)',
                            }}
                        >
                            <Send size={14} color={loading || (!input.trim() && !selectedImage) ? 'var(--color-primary-200)' : '#fff'} />
                        </button>
                    </div>
                    <input ref={fileInputRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={handleImageUpload} />
                </div>
            )}
        </>
    )
}
