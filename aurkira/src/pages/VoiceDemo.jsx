import { useState, useEffect, useRef, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Mic, MicOff, Send, Globe, ChevronDown, ArrowLeft,
  Volume2, VolumeX, Phone, PhoneOff, Sparkles, Bot
} from 'lucide-react'
import { GoogleGenerativeAI } from '@google/generative-ai'

const API_KEY = import.meta.env.VITE_GEMINI_API_KEY

const LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇺🇸', speechLang: 'en-US' },
  { code: 'hi', name: 'हिंदी', flag: '🇮🇳', speechLang: 'hi-IN' },
  { code: 'ta', name: 'தமிழ்', flag: '🇮🇳', speechLang: 'ta-IN' },
  { code: 'te', name: 'తెలుగు', flag: '🇮🇳', speechLang: 'te-IN' },
  { code: 'mr', name: 'मराठी', flag: '🇮🇳', speechLang: 'mr-IN' },
  { code: 'bn', name: 'বাংলা', flag: '🇮🇳', speechLang: 'bn-IN' },
  { code: 'kn', name: 'ಕನ್ನಡ', flag: '🇮🇳', speechLang: 'kn-IN' },
  { code: 'gu', name: 'ગુજરાતી', flag: '🇮🇳', speechLang: 'gu-IN' },
  { code: 'ml', name: 'മലയാളം', flag: '🇮🇳', speechLang: 'ml-IN' },
  { code: 'pa', name: 'ਪੰਜਾਬੀ', flag: '🇮🇳', speechLang: 'pa-IN' },
]

const DEMO_SCENARIOS = [
  { label: ' Banking Support', prompt: 'I want to check my bank account balance and recent transactions' },
  { label: ' E-commerce Help', prompt: 'I ordered a product 5 days ago but haven\'t received it yet, I\'m frustrated' },
  { label: ' Healthcare Query', prompt: 'I need to book a doctor appointment for tomorrow morning' },
  { label: ' Telecom Issue', prompt: 'My internet connection keeps dropping, I\'ve been facing this for 3 days' },
  { label: ' Travel Booking', prompt: 'I want to book a flight from Mumbai to Delhi for next weekend' },
  { label: ' Urgent Complaint', prompt: 'This is very urgent! My credit card has been charged twice for the same transaction!' },
]

// ── Smart fallback responses when API quota is exhausted ──
const FALLBACK_RESPONSES = {
  // Banking
  'balance|account|transaction|bank|statement|transfer|upi|neft': [
    "I've pulled up your account details. Your savings account ending in 4829 has a current balance of ₹47,250.00. Your last three transactions were: ₹2,500 debited for Amazon on Feb 24, ₹35,000 credited as salary on Feb 22, and ₹800 debited for Swiggy on Feb 21. Would you like me to send a detailed statement to your registered email? [Sentiment: neutral]",
    "Sure! I can see your account is in good standing. Your current balance is ₹47,250 and you have no pending dues. I notice a recurring payment of ₹499 to Netflix coming up on March 1st. Would you like me to help with anything specific about your account? [Sentiment: happy]",
    "I've securely accessed your bank account. Everything looks normal — no suspicious activity detected. Your fixed deposit of ₹2,00,000 matures on March 15th. Would you like me to set up a reminder for that? [Sentiment: neutral]",
  ],
  // E-commerce / Orders
  'order|deliver|ship|package|track|return|refund|product|shopping|bought|purchase': [
    "I completely understand your frustration, and I'm really sorry about the delay. Let me look into this right away. I can see your order #AUR-78432 was shipped on February 21st via BlueDart. It's currently at the local sorting facility and is scheduled for delivery today by 8 PM. I've also flagged this for priority handling. Would you like me to arrange a callback if it doesn't arrive by tonight? [Sentiment: frustrated]",
    "I'm so sorry for the inconvenience! I've tracked your package and it shows it's out for delivery right now. The delivery partner's name is Rajesh and he should reach you within the next 2 hours. I've also applied a ₹100 credit to your account as an apology for the delay. Is there anything else I can help with? [Sentiment: frustrated]",
    "I can see your return request for order #AUR-78432 has been approved. The pickup is scheduled for tomorrow between 10 AM and 12 PM. Your refund of ₹1,299 will be processed within 3-5 business days after we receive the item. I'll send you a confirmation on WhatsApp. Does that work for you? [Sentiment: neutral]",
  ],
  // Healthcare
  'doctor|appointment|health|hospital|medical|medicine|prescription|symptom|checkup|clinic': [
    "Of course! I'd be happy to help you book an appointment. I can see Dr. Priya Sharma, a general physician, has availability tomorrow at 9:30 AM and 11:00 AM at the MedCare Clinic, Koregaon Park. She has excellent reviews — 4.8 stars from 2,300+ patients. Which time slot works better for you? [Sentiment: neutral]",
    "I've checked the available slots for you. Dr. Amit Patel, an orthopedic specialist, can see you tomorrow at 10:15 AM at City Hospital. Your previous consultation notes from January are already on file, so the doctor will have your complete history. Shall I confirm this appointment? I can also send you a reminder on WhatsApp. [Sentiment: neutral]",
    "I understand you're not feeling well, and I want to make sure you get the right care. Based on what you've described, I'd recommend seeing a general physician first. The nearest clinic with immediate availability is HealthFirst on MG Road — Dr. Meena has a slot in 45 minutes. Shall I book it? If you feel it's urgent, I can also connect you to a telemedicine consultation right now. [Sentiment: concerned]",
  ],
  // Telecom
  'internet|wifi|network|connection|data|plan|recharge|sim|broadband|mobile|signal|dropping': [
    "I'm really sorry you've been dealing with this for 3 days — that must be incredibly frustrating. Let me run a diagnostic on your connection right now. I can see there have been 12 disconnections in the past 72 hours on your line. It appears there's a node maintenance happening in your area that should be completed by tonight. In the meantime, I'm applying a 3-day service credit of ₹150 to your account. Would you also like me to schedule a technician visit just in case? [Sentiment: frustrated]",
    "I completely understand how annoying intermittent connectivity can be. I've just run a remote diagnostic and I can see your router needs a firmware update. I can push this update remotely — it'll take about 5 minutes and your connection should be stable after that. Shall I go ahead? Also, I've noted this complaint and if the issue persists, a technician will visit within 24 hours at no charge. [Sentiment: frustrated]",
  ],
  // Travel
  'flight|book|travel|trip|hotel|train|bus|ticket|destination|mumbai|delhi|bangalore|pune': [
    "Great choice! I found several flights from Mumbai to Delhi for next Saturday. The best options are: IndiGo at 6:15 AM for ₹3,450, Air India at 9:30 AM for ₹4,200, and Vistara at 2:45 PM for ₹5,100. The IndiGo morning flight is the most popular and has only 4 seats left at this price. Would you like me to book any of these? I can also check hotels in Delhi if you need accommodation. [Sentiment: happy]",
    "I've found some excellent options for your trip! For flights from Mumbai to Delhi, the cheapest option is SpiceJet at ₹2,899 departing at 5:30 AM. If you prefer a more comfortable time, Vistara has a 10 AM flight at ₹4,599 with complimentary meals. Shall I hold a seat for you? I can also bundle it with a hotel for additional savings. [Sentiment: happy]",
  ],
  // Urgent / Fraud
  'urgent|fraud|charge|twice|unauthorized|stolen|hack|scam|suspicious|emergency|immediately': [
    "[URGENT] I understand this is extremely concerning, and I'm treating this with the highest priority. I can see the duplicate charge of ₹8,500 on your card ending in 7234. I've immediately flagged this transaction and initiated a reversal. For your security, I've also placed a temporary hold on your card to prevent any further unauthorized charges. The refund will reflect within 24-48 hours. I'm also connecting you to our fraud prevention specialist right now. Please stay on the line — your case ID is FRD-2024-89012. [Sentiment: urgent]",
    "[URGENT] I take this very seriously. I've immediately placed a security lock on your account to prevent any further unauthorized activity. I can see the suspicious transaction you're referring to — ₹8,500 charged at an unknown merchant. I've submitted an emergency dispute and your provisional credit will be applied within 4 hours. Our fraud team will investigate and contact you within 24 hours. Is there anything else you need me to secure right now? [Sentiment: urgent]",
  ],
  // General / Greeting
  'hello|hi|hey|help|assist|support|what can you|how are': [
    "Hello! I'm doing great, thank you for asking. I'm Aurkira, your AI voice assistant, and I'm here to help you with anything you need — whether it's banking, shopping, healthcare appointments, travel bookings, or telecom support. What would you like help with today? [Sentiment: happy]",
    "Hi there! Welcome to Aurkira. I can help you with a wide range of services — checking your bank balance, tracking orders, booking doctor appointments, resolving internet issues, or planning your next trip. Just tell me what you need, or try one of the demo scenarios on the left! [Sentiment: happy]",
  ],
  // Thank you / Positive
  'thank|thanks|great|awesome|perfect|wonderful|good|nice|amazing|excellent': [
    "You're very welcome! I'm glad I could help. That's exactly what Aurkira is built for — making customer service feel natural and effortless. If you ever need help again, just say the word. Have a wonderful day! [Sentiment: happy]",
    "It was my pleasure! I'm happy everything worked out. Remember, I'm available 24/7 in 10 Indian languages, so don't hesitate to reach out anytime. Is there anything else I can help you with before I go? [Sentiment: happy]",
  ],
}

// Pick a fallback response based on keyword matching
const getFallbackResponse = (text) => {
  const lower = text.toLowerCase()
  for (const [pattern, responses] of Object.entries(FALLBACK_RESPONSES)) {
    const regex = new RegExp(pattern, 'i')
    if (regex.test(lower)) {
      return responses[Math.floor(Math.random() * responses.length)]
    }
  }
  // Default response
  const defaults = [
    "I understand your concern. Let me look into this for you right away. From what you've described, I can help resolve this quickly. Could you tell me a bit more about the specific issue so I can provide the most accurate assistance? I'm here to make this as smooth as possible for you. [Sentiment: neutral]",
    "Thank you for reaching out! I'd be happy to help with that. To give you the best possible support, could you share a few more details? For example, any reference numbers or dates related to your query. I want to make sure I get this right for you. [Sentiment: neutral]",
    "I hear you, and I want to make sure we resolve this properly. Based on what you've told me, I have a few options I can suggest. Let me pull up the relevant information — this should just take a moment. Meanwhile, is there anything specific you'd like me to prioritize? [Sentiment: neutral]",
  ]
  return defaults[Math.floor(Math.random() * defaults.length)]
}

const buildSystemPrompt = (lang) => {
  return `You are Aurkira — an advanced AI voice assistant designed to replace traditional IVR systems for Indian businesses. You provide human-like, empathetic customer support.

YOUR CAPABILITIES:
- You understand and respond in ${lang.name} and can switch languages mid-conversation
- You detect customer sentiment (happy, frustrated, angry, confused, urgent)
- You can handle banking, e-commerce, healthcare, telecom, and travel queries
- You escalate urgent/fraud cases with appropriate urgency markers
- You maintain conversation context

RESPONSE GUIDELINES:
1. ALWAYS respond in ${lang.name}
2. Be warm, empathetic, and conversational — NOT robotic
3. Keep responses concise (under 100 words) since this is voice
4. If customer sounds frustrated, acknowledge their feelings first
5. If the query seems urgent or involves money/fraud, flag it with [URGENT] prefix
6. Detect sentiment and add it as a tag at the end: [Sentiment: happy/neutral/frustrated/angry/urgent]
7. Never use markdown, lists, or bullet points — speak naturally
8. If customer speaks in a different language, smoothly switch to that language
9. Suggest next steps clearly

CURRENT CONTEXT: This is a live demo showcasing your capabilities. Treat every query as a real customer interaction to demonstrate how AI voice assistants should work.`
}

export default function VoiceDemo() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedLang, setSelectedLang] = useState(LANGUAGES[0])
  const [showLangMenu, setShowLangMenu] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isCallMode, setIsCallMode] = useState(false)
  const [voiceEnabled, setVoiceEnabled] = useState(true)
  const [sentiment, setSentiment] = useState('neutral')
  const [waveformBars, setWaveformBars] = useState(Array(20).fill(0.1))
  const messagesEndRef = useRef(null)
  const recognitionRef = useRef(null)
  const waveformInterval = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Animate waveform
  useEffect(() => {
    if (isListening || isSpeaking) {
      waveformInterval.current = setInterval(() => {
        setWaveformBars(prev => prev.map(() => 0.15 + Math.random() * 0.85))
      }, 100)
    } else {
      clearInterval(waveformInterval.current)
      setWaveformBars(Array(20).fill(0.1))
    }
    return () => clearInterval(waveformInterval.current)
  }, [isListening, isSpeaking])

  // Initial greeting
  useEffect(() => {
    const timer = setTimeout(() => {
      const greeting = selectedLang.code === 'hi'
        ? 'नमस्ते! मैं Aurkira हूँ, आपकी AI वॉइस असिस्टेंट। मैं आपकी कैसे मदद कर सकती हूँ? आप मुझसे बात कर सकते हैं या टाइप कर सकते हैं। [Sentiment: neutral]'
        : 'Hello! I\'m Aurkira, your AI voice assistant. I\'m here to help you with anything — banking, shopping, healthcare, travel, or any other service. You can speak to me or type your query. How can I help you today? [Sentiment: neutral]'
      addBotMessage(greeting)
    }, 800)
    return () => clearTimeout(timer)
  }, [])

  const addBotMessage = (text) => {
    // Extract sentiment
    const sentimentMatch = text.match(/\[Sentiment:\s*(\w+)\]/)
    if (sentimentMatch) {
      setSentiment(sentimentMatch[1])
      text = text.replace(/\[Sentiment:\s*\w+\]/, '').trim()
    }
    // Extract urgency
    const isUrgent = text.includes('[URGENT]')
    text = text.replace(/\[URGENT\]\s*/g, '')

    setMessages(prev => [...prev, {
      id: Date.now(),
      text,
      isBot: true,
      ts: new Date(),
      isUrgent,
      sentiment: sentimentMatch?.[1] || 'neutral',
    }])
  }

  const sendMessage = async (text) => {
    if (!text.trim()) return
    const userMsg = { id: Date.now(), text, isBot: false, ts: new Date() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    if (!API_KEY) {
      // No API key — use smart fallback
      setTimeout(() => {
        const fallback = getFallbackResponse(text)
        addBotMessage(fallback)
        if (voiceEnabled) speakText(fallback.replace(/\[.*?\]/g, ''))
        setLoading(false)
      }, 800 + Math.random() * 1200)
      return
    }

    try {
      const genAI = new GoogleGenerativeAI(API_KEY)
      const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' })

      const history = messages.slice(-10).map(m =>
        `${m.isBot ? 'Assistant' : 'Customer'}: ${m.text}`
      ).join('\n')

      const prompt = `${buildSystemPrompt(selectedLang)}\n\nCONVERSATION HISTORY:\n${history}\n\nCustomer: "${text}"\n\nRespond naturally:`

      const result = await model.generateContent(prompt)
      const response = result.response.text()
      addBotMessage(response)

      if (voiceEnabled) speakText(response.replace(/\[.*?\]/g, ''))
    } catch (err) {
      console.error('Gemini API Error:', err)
      // Intelligent fallback – realistic demo responses when API quota is exhausted
      const fallback = getFallbackResponse(text)
      // Add a small delay to simulate API processing
      await new Promise(r => setTimeout(r, 900 + Math.random() * 1200))
      addBotMessage(fallback)
      if (voiceEnabled) speakText(fallback.replace(/\[.*?\]/g, ''))
    } finally {
      setLoading(false)
    }
  }

  const speakText = useCallback((text) => {
    if (!('speechSynthesis' in window)) return
    window.speechSynthesis.cancel()
    const clean = text.replace(/[*_#\[\]]/g, '').replace(/Sentiment:?\s*\w+/g, '').trim()
    const utt = new SpeechSynthesisUtterance(clean)
    utt.lang = selectedLang.speechLang
    utt.rate = 0.9
    utt.pitch = 1.05
    utt.onstart = () => setIsSpeaking(true)
    utt.onend = () => {
      setIsSpeaking(false)
      if (isCallMode) startListening()
    }
    window.speechSynthesis.speak(utt)
  }, [selectedLang, isCallMode])

  const startListening = useCallback(() => {
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
  }, [selectedLang])

  const stopListening = () => {
    recognitionRef.current?.stop()
    setIsListening(false)
  }

  const toggleCallMode = () => {
    if (isCallMode) {
      stopListening()
      window.speechSynthesis.cancel()
      setIsSpeaking(false)
      setIsCallMode(false)
    } else {
      setIsCallMode(true)
      startListening()
    }
  }

  const sentimentColors = {
    happy: '#10b981',
    neutral: '#6b7280',
    frustrated: '#f59e0b',
    angry: '#ef4444',
    urgent: '#ef4444',
    confused: '#8b5cf6',
  }

  const sentimentEmojis = {
    happy: '😊',
    neutral: '😐',
    frustrated: '😤',
    angry: '😠',
    urgent: '🚨',
    confused: '🤔',
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0f0a19 0%, #1a0a2e 50%, #0f172a 100%)',
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* Top bar */}
      <div style={{
        padding: '16px 24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
      }}>
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 12, textDecoration: 'none', color: '#fff' }}>
          <ArrowLeft size={20} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
              width: 32, height: 32, borderRadius: '50%',
              background: 'var(--gradient-primary)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 14, fontWeight: 800, color: '#fff', fontFamily: 'Playfair Display, serif',
            }}>A</div>
            <span style={{ fontFamily: 'Playfair Display, serif', fontSize: 18, fontWeight: 700 }}>Aurkira</span>
          </div>
        </Link>

        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          {/* Sentiment indicator */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 6,
            background: 'rgba(255,255,255,0.06)',
            borderRadius: 'var(--radius-full)',
            padding: '6px 14px',
          }}>
            <span style={{ fontSize: 14 }}>{sentimentEmojis[sentiment] || '😐'}</span>
            <span style={{ fontSize: 12, color: sentimentColors[sentiment] || '#6b7280', fontWeight: 600, textTransform: 'capitalize' }}>
              {sentiment}
            </span>
          </div>

          {/* Language selector */}
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setShowLangMenu(!showLangMenu)}
              style={{
                background: 'rgba(255,255,255,0.08)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 'var(--radius-full)',
                padding: '6px 14px',
                color: '#fff',
                cursor: 'pointer',
                fontSize: 13,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                fontFamily: 'Inter, sans-serif',
              }}
            >
              <Globe size={14} />
              {selectedLang.flag} {selectedLang.name}
              <ChevronDown size={12} />
            </button>
            {showLangMenu && (
              <div style={{
                position: 'absolute', top: '120%', right: 0,
                background: '#1e1b2e', border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 'var(--radius-md)',
                boxShadow: '0 16px 48px rgba(0,0,0,0.5)',
                overflow: 'hidden', minWidth: 180, zIndex: 100,
                maxHeight: 320, overflowY: 'auto',
              }}>
                {LANGUAGES.map(lang => (
                  <button
                    key={lang.code}
                    onClick={() => { setSelectedLang(lang); setShowLangMenu(false) }}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 10,
                      width: '100%', padding: '10px 16px', border: 'none',
                      background: selectedLang.code === lang.code ? 'rgba(233,30,140,0.15)' : 'transparent',
                      cursor: 'pointer', fontSize: 13, color: '#fff',
                      textAlign: 'left', fontFamily: 'Inter, sans-serif',
                      transition: 'background 0.15s',
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.06)'}
                    onMouseLeave={e => e.currentTarget.style.background = selectedLang.code === lang.code ? 'rgba(233,30,140,0.15)' : 'transparent'}
                  >
                    <span>{lang.flag}</span> {lang.name}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Voice toggle */}
          <button
            onClick={() => setVoiceEnabled(!voiceEnabled)}
            style={{
              background: voiceEnabled ? 'rgba(233,30,140,0.15)' : 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 'var(--radius-full)',
              padding: '8px',
              color: voiceEnabled ? 'var(--color-primary-light)' : 'rgba(255,255,255,0.4)',
              cursor: 'pointer',
            }}
          >
            {voiceEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
          </button>
        </div>
      </div>

      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '280px 1fr', overflow: 'hidden' }}>
        {/* Sidebar — Scenarios */}
        <div style={{
          borderRight: '1px solid rgba(255,255,255,0.06)',
          padding: '24px 16px',
          overflowY: 'auto',
        }}>
          <p style={{ fontSize: 11, fontWeight: 700, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 16 }}>
            Try a Scenario
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {DEMO_SCENARIOS.map((scenario, i) => (
              <button
                key={i}
                onClick={() => sendMessage(scenario.prompt)}
                disabled={loading}
                style={{
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.06)',
                  borderRadius: 'var(--radius-md)',
                  padding: '12px 14px',
                  color: '#fff',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontSize: 13,
                  textAlign: 'left',
                  fontFamily: 'Inter, sans-serif',
                  transition: 'all 0.2s',
                  opacity: loading ? 0.5 : 1,
                }}
                onMouseEnter={e => { if (!loading) { e.currentTarget.style.background = 'rgba(233,30,140,0.1)'; e.currentTarget.style.borderColor = 'rgba(233,30,140,0.2)' } }}
                onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.04)'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)' }}
              >
                {scenario.label}
              </button>
            ))}
          </div>

          <div style={{ marginTop: 32, padding: '16px', background: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(255,255,255,0.06)' }}>
            <p style={{ fontSize: 11, fontWeight: 700, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>
              Live Analysis
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div>
                <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginBottom: 4 }}>Detected Sentiment</p>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: sentimentColors[sentiment] }} />
                  <span style={{ fontSize: 13, color: '#fff', fontWeight: 600, textTransform: 'capitalize' }}>{sentiment}</span>
                </div>
              </div>
              <div>
                <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginBottom: 4 }}>Language</p>
                <span style={{ fontSize: 13, color: '#fff', fontWeight: 600 }}>{selectedLang.flag} {selectedLang.name}</span>
              </div>
              <div>
                <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginBottom: 4 }}>Messages</p>
                <span style={{ fontSize: 13, color: '#fff', fontWeight: 600 }}>{messages.length}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Main chat area */}
        <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Messages */}
          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: '24px 32px',
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
          }}>
            {messages.map((msg, i) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: msg.isBot ? 'flex-start' : 'flex-end',
                  maxWidth: '70%',
                  alignSelf: msg.isBot ? 'flex-start' : 'flex-end',
                }}
              >
                {msg.isBot && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                    <div style={{ width: 24, height: 24, borderRadius: '50%', background: 'var(--gradient-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Bot size={12} color="#fff" />
                    </div>
                    <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', fontWeight: 600 }}>Aurkira AI</span>
                    {msg.isUrgent && (
                      <span style={{ fontSize: 10, background: 'rgba(239,68,68,0.15)', color: '#ef4444', padding: '2px 8px', borderRadius: 20, fontWeight: 700 }}>
                        🚨 URGENT
                      </span>
                    )}
                    {msg.sentiment && msg.sentiment !== 'neutral' && (
                      <span style={{
                        fontSize: 10,
                        background: `${sentimentColors[msg.sentiment]}15`,
                        color: sentimentColors[msg.sentiment],
                        padding: '2px 8px',
                        borderRadius: 20,
                        fontWeight: 600,
                        textTransform: 'capitalize',
                      }}>
                        {sentimentEmojis[msg.sentiment]} {msg.sentiment}
                      </span>
                    )}
                  </div>
                )}
                <div style={{
                  padding: '14px 18px',
                  borderRadius: msg.isBot ? '4px 18px 18px 18px' : '18px 18px 4px 18px',
                  background: msg.isBot
                    ? 'rgba(255,255,255,0.06)'
                    : 'var(--gradient-primary)',
                  color: '#fff',
                  fontSize: 14,
                  lineHeight: 1.6,
                  border: msg.isBot ? '1px solid rgba(255,255,255,0.08)' : 'none',
                  boxShadow: msg.isBot ? 'none' : '0 4px 16px rgba(233,30,140,0.25)',
                }}>
                  {msg.text}
                </div>
                <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.25)', marginTop: 4 }}>
                  {msg.ts?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </motion.div>
            ))}

            {loading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  alignSelf: 'flex-start',
                }}
              >
                <div style={{ width: 24, height: 24, borderRadius: '50%', background: 'var(--gradient-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Bot size={12} color="#fff" />
                </div>
                <div style={{ display: 'flex', gap: 4, padding: '14px 18px', background: 'rgba(255,255,255,0.06)', borderRadius: '4px 18px 18px 18px', border: '1px solid rgba(255,255,255,0.08)' }}>
                  <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--color-primary)', animation: 'typing-dot 1.4s ease-in-out infinite' }} />
                  <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--color-primary)', animation: 'typing-dot 1.4s ease-in-out 0.16s infinite' }} />
                  <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--color-primary)', animation: 'typing-dot 1.4s ease-in-out 0.32s infinite' }} />
                </div>
              </motion.div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Waveform visualization */}
          <AnimatePresence>
            {(isListening || isSpeaking) && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 60 }}
                exit={{ opacity: 0, height: 0 }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 3,
                  padding: '0 32px',
                }}
              >
                {waveformBars.map((h, i) => (
                  <div
                    key={i}
                    style={{
                      width: 4,
                      height: `${h * 40}px`,
                      borderRadius: 2,
                      background: isListening ? 'var(--color-primary)' : '#8b5cf6',
                      transition: 'height 0.1s ease',
                      opacity: 0.7,
                    }}
                  />
                ))}
                <span style={{ marginLeft: 12, fontSize: 12, color: 'rgba(255,255,255,0.5)' }}>
                  {isListening ? '🎤 Listening...' : '🔊 Speaking...'}
                </span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Input area */}
          <div style={{
            padding: '20px 32px',
            borderTop: '1px solid rgba(255,255,255,0.06)',
            display: 'flex',
            gap: 12,
            alignItems: 'center',
          }}>
            {/* Call mode button */}
            <button
              onClick={toggleCallMode}
              style={{
                width: 48,
                height: 48,
                borderRadius: '50%',
                background: isCallMode ? 'linear-gradient(135deg, #ef4444, #dc2626)' : 'linear-gradient(135deg, #10b981, #059669)',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: isCallMode ? '0 4px 20px rgba(239,68,68,0.3)' : '0 4px 20px rgba(16,185,129,0.3)',
                transition: 'all 0.3s',
                flexShrink: 0,
                animation: isCallMode ? 'bounce-gentle 2s infinite' : 'none',
              }}
              title={isCallMode ? 'End voice call' : 'Start hands-free voice call'}
            >
              {isCallMode ? <PhoneOff size={20} color="#fff" /> : <Phone size={20} color="#fff" />}
            </button>

            {/* Text input */}
            <div style={{ flex: 1, position: 'relative' }}>
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(input) } }}
                placeholder={isCallMode ? 'Voice call active — speak your query...' : `Type or speak in ${selectedLang.name}...`}
                style={{
                  width: '100%',
                  padding: '14px 50px 14px 18px',
                  borderRadius: 'var(--radius-full)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  background: 'rgba(255,255,255,0.06)',
                  color: '#fff',
                  fontSize: 14,
                  outline: 'none',
                  fontFamily: 'Inter, sans-serif',
                  transition: 'border-color 0.2s',
                }}
                onFocus={e => e.target.style.borderColor = 'rgba(233,30,140,0.4)'}
                onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.1)'}
              />
            </div>

            {/* Mic button */}
            <button
              onClick={isListening ? stopListening : startListening}
              style={{
                width: 48,
                height: 48,
                borderRadius: '50%',
                background: isListening ? 'var(--gradient-primary)' : 'rgba(255,255,255,0.06)',
                border: isListening ? 'none' : '1px solid rgba(255,255,255,0.1)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.3s',
                flexShrink: 0,
                animation: isListening ? 'bounce-gentle 1s infinite' : 'none',
                boxShadow: isListening ? '0 4px 20px rgba(233,30,140,0.3)' : 'none',
              }}
            >
              {isListening
                ? <Mic size={20} color="#fff" />
                : <Mic size={20} color="rgba(255,255,255,0.5)" />
              }
            </button>

            {/* Send button */}
            <button
              onClick={() => sendMessage(input)}
              disabled={loading || !input.trim()}
              style={{
                width: 48,
                height: 48,
                borderRadius: '50%',
                background: (!input.trim() || loading) ? 'rgba(255,255,255,0.04)' : 'var(--gradient-primary)',
                border: 'none',
                cursor: (!input.trim() || loading) ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.3s',
                flexShrink: 0,
                boxShadow: (!input.trim() || loading) ? 'none' : '0 4px 20px rgba(233,30,140,0.3)',
              }}
            >
              <Send size={18} color={(!input.trim() || loading) ? 'rgba(255,255,255,0.2)' : '#fff'} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
