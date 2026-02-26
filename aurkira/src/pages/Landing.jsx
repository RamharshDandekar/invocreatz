import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Mic, Globe, Brain, Shield, BarChart3, Zap,
  Phone, MessageSquare, Building2, Languages,
  ArrowRight, Play, CheckCircle, Star, TrendingUp,
  HeadphonesIcon, Bot, Sparkles
} from 'lucide-react'

const stats = [
  { value: '95%', label: 'Customer Satisfaction', icon: Star },
  { value: '40%', label: 'Cost Reduction', icon: TrendingUp },
  { value: '24/7', label: 'Always Available', icon: HeadphonesIcon },
  { value: '10+', label: 'Indian Languages', icon: Languages },
]

const features = [
  {
    icon: Mic,
    title: 'Natural Voice Understanding',
    desc: 'Understands natural speech patterns, accents, and colloquial language across Hindi, Tamil, Telugu, Marathi, Bengali, and more.',
    color: '#e91e8c',
  },
  {
    icon: Brain,
    title: 'Emotional Intelligence',
    desc: 'Detects customer sentiment, urgency, and frustration in real-time. Adapts tone and responses accordingly.',
    color: '#8b5cf6',
  },
  {
    icon: Globe,
    title: 'Multilingual Support',
    desc: 'Seamlessly switches between 10+ Indian regional languages mid-conversation without losing context.',
    color: '#0ea5e9',
  },
  {
    icon: Shield,
    title: 'Fraud Detection',
    desc: 'AI-powered pattern recognition identifies suspicious interactions and flags potential fraud in real-time.',
    color: '#f59e0b',
  },
  {
    icon: BarChart3,
    title: 'Analytics Dashboard',
    desc: 'Real-time insights on call volumes, sentiment trends, resolution rates, and customer satisfaction scores.',
    color: '#10b981',
  },
  {
    icon: Zap,
    title: 'Instant Integration',
    desc: 'Plug-and-play with CRM, WhatsApp Business, ERP systems, and websites. API-first architecture.',
    color: '#ef4444',
  },
]

const problems = [
  { emoji: '1', text: 'Press 1, Press 2... customers hate IVR menus' },
  { emoji: '2', text: 'High call drop rates (avg 60% abandon IVR calls)' },
  { emoji: '3', text: 'Increased operational costs for call centers' },
  { emoji: '4', text: 'No support for regional languages in rural India' },
  { emoji: '5', text: 'Robotic responses that frustrate customers' },
  { emoji: '6', text: 'Lost sales from poor customer experience' },
]

const integrations = [
  { name: 'WhatsApp', color: '#25D366' },
  { name: 'CRM', color: '#e91e8c' },
  { name: 'ERP', color: '#8b5cf6' },
  { name: 'Websites', color: '#0ea5e9' },
  { name: 'Telephony', color: '#f59e0b' },
  { name: 'Analytics', color: '#10b981' },
]

const fadeInUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6 } },
}

const stagger = {
  visible: { transition: { staggerChildren: 0.1 } },
}

export default function Landing() {
  const [activeWord, setActiveWord] = useState(0)
  const words = ['Human-Like', 'Multilingual', 'Intelligent', 'Empathetic']

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveWord((prev) => (prev + 1) % words.length)
    }, 2500)
    return () => clearInterval(interval)
  }, [])

  return (
    <div>
      {/* ===== HERO ===== */}
      <section style={{
        minHeight: '90vh',
        display: 'flex',
        alignItems: 'center',
        position: 'relative',
        overflow: 'hidden',
        background: 'linear-gradient(135deg, #fff0f6 0%, #f5f3ff 50%, #eff6ff 100%)',
      }}>
        {/* Floating shapes */}
        <div style={{ position: 'absolute', top: '10%', right: '5%', width: 300, height: 300, borderRadius: '50%', background: 'radial-gradient(circle, rgba(233,30,140,0.06) 0%, transparent 70%)', pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', bottom: '10%', left: '5%', width: 200, height: 200, borderRadius: '50%', background: 'radial-gradient(circle, rgba(139,92,246,0.06) 0%, transparent 70%)', pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', top: '40%', left: '60%', width: 150, height: 150, borderRadius: '50%', background: 'radial-gradient(circle, rgba(14,165,233,0.06) 0%, transparent 70%)', pointerEvents: 'none' }} />

        <div className="container" style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 60, alignItems: 'center' }}>
            {/* Left */}
            <motion.div initial="hidden" animate="visible" variants={stagger}>
              <motion.div variants={fadeInUp} style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: 'rgba(233,30,140,0.08)', border: '1px solid rgba(233,30,140,0.15)', borderRadius: 'var(--radius-full)', padding: '6px 16px', marginBottom: 24 }}>
                <Sparkles size={14} color="var(--color-primary)" />
                <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-primary)' }}>AI-Powered Voice Assistant</span>
              </motion.div>

              <motion.h1 variants={fadeInUp} style={{
                fontFamily: 'Playfair Display, serif',
                fontSize: 'clamp(36px, 5vw, 60px)',
                fontWeight: 700,
                lineHeight: 1.15,
                marginBottom: 24,
                color: 'var(--color-text)',
              }}>
                The{' '}
                <span style={{
                  background: 'var(--gradient-primary)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  display: 'inline-block',
                  minWidth: 280,
                }}>
                  {words[activeWord]}
                </span>
                <br />
                Voice Chatbot for
                <br />
                Your Business
              </motion.h1>

              <motion.p variants={fadeInUp} style={{
                fontSize: 18,
                color: 'var(--color-text-secondary)',
                lineHeight: 1.7,
                marginBottom: 36,
                maxWidth: 520,
              }}>
                Replace frustrating IVR systems with a truly intelligent AI voice assistant
                that speaks regional Indian languages, understands emotions, and works 24/7 —
                no human intervention needed.
              </motion.p>

              <motion.div variants={fadeInUp} style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                <Link to="/demo" className="btn btn-primary" style={{ fontSize: 16, padding: '14px 32px' }}>
                  <Play size={18} /> Try Live Demo
                </Link>
                <a href="#features" className="btn btn-outline" style={{ fontSize: 16, padding: '14px 32px' }}>
                  Learn More <ArrowRight size={18} />
                </a>
              </motion.div>

              <motion.div variants={fadeInUp} style={{ display: 'flex', gap: 24, marginTop: 40 }}>
                {['Hindi', 'Tamil', 'Telugu', 'Marathi', 'Bengali'].map(lang => (
                  <span key={lang} style={{ fontSize: 13, color: 'var(--color-text-muted)', fontWeight: 500 }}>
                    🗣️ {lang}
                  </span>
                ))}
              </motion.div>
            </motion.div>

            {/* Right — Voice visualization */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8, delay: 0.3 }}
              style={{ display: 'flex', justifyContent: 'center' }}
            >
              <div style={{
                width: 400,
                height: 400,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, rgba(233,30,140,0.08) 0%, rgba(139,92,246,0.08) 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                position: 'relative',
              }}>
                {/* Outer ring */}
                <div style={{
                  position: 'absolute',
                  width: 360,
                  height: 360,
                  borderRadius: '50%',
                  border: '2px solid rgba(233,30,140,0.1)',
                  animation: 'spin-slow 20s linear infinite',
                }} />
                {/* Middle ring */}
                <div style={{
                  position: 'absolute',
                  width: 300,
                  height: 300,
                  borderRadius: '50%',
                  border: '2px dashed rgba(139,92,246,0.12)',
                  animation: 'spin-slow 15s linear infinite reverse',
                }} />
                {/* Inner circle */}
                <div style={{
                  width: 200,
                  height: 200,
                  borderRadius: '50%',
                  background: 'var(--gradient-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 0 60px rgba(233,30,140,0.25)',
                  animation: 'bounce-gentle 3s ease-in-out infinite',
                  cursor: 'pointer',
                }}>
                  <Link to="/demo" style={{ textDecoration: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                    <Mic size={48} color="#fff" />
                    <span style={{ color: '#fff', fontSize: 14, fontWeight: 600 }}>Try Now</span>
                  </Link>
                </div>

                {/* Floating badges */}
                {[
                  { label: 'Hindi 🇮🇳', top: '5%', left: '10%' },
                  { label: 'Tamil', top: '15%', right: '-5%' },
                  { label: 'Sentiment AI', bottom: '15%', right: '0%' },
                  { label: 'WhatsApp', bottom: '5%', left: '10%' },
                ].map((badge, i) => (
                  <motion.div
                    key={badge.label}
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.8 + i * 0.15, type: 'spring' }}
                    style={{
                      position: 'absolute',
                      ...badge,
                      background: '#fff',
                      boxShadow: 'var(--shadow-md)',
                      borderRadius: 'var(--radius-full)',
                      padding: '6px 14px',
                      fontSize: 12,
                      fontWeight: 600,
                      color: 'var(--color-text)',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {badge.label}
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ===== STATS BAR ===== */}
      <section style={{ background: 'var(--color-text)', padding: '48px 0' }}>
        <div className="container">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 32, textAlign: 'center' }}>
            {stats.map((stat, i) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                viewport={{ once: true }}
              >
                <stat.icon size={24} color="var(--color-primary-light)" style={{ marginBottom: 8 }} />
                <p style={{ fontSize: 36, fontWeight: 800, color: '#fff', fontFamily: 'Playfair Display, serif' }}>{stat.value}</p>
                <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.6)' }}>{stat.label}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== PROBLEM ===== */}
      <section style={{ padding: '80px 0', background: '#fff' }}>
        <div className="container">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={stagger}
            style={{ textAlign: 'center', marginBottom: 48 }}
          >
            <motion.h2 variants={fadeInUp} className="section-title">
              The Problem with Traditional IVR
            </motion.h2>
            <motion.p variants={fadeInUp} className="section-subtitle" style={{ maxWidth: 600, margin: '0 auto 48px' }}>
              In India, 70% of customers prefer voice over text — yet businesses force them
              through robotic menu systems that nobody likes.
            </motion.p>
          </motion.div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20 }}>
            {problems.map((p, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
                viewport={{ once: true }}
                style={{
                  background: '#fff',
                  border: '1px solid var(--color-border-light)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '24px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                  transition: 'all var(--transition)',
                }}
                onMouseEnter={e => { e.currentTarget.style.boxShadow = 'var(--shadow-md)'; e.currentTarget.style.borderColor = 'var(--color-primary-100)' }}
                onMouseLeave={e => { e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.borderColor = 'var(--color-border-light)' }}
              >
                <span style={{ fontSize: 28 }}>{p.emoji}</span>
                <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', fontWeight: 500, lineHeight: 1.5 }}>{p.text}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== FEATURES ===== */}
      <section id="features" style={{ padding: '80px 0', background: 'var(--color-bg-soft)' }}>
        <div className="container">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={stagger}
            style={{ textAlign: 'center', marginBottom: 56 }}
          >
            <motion.h2 variants={fadeInUp} className="section-title">
              Why Aurkira is Different
            </motion.h2>
            <motion.p variants={fadeInUp} className="section-subtitle" style={{ maxWidth: 600, margin: '0 auto' }}>
              Built from the ground up for Indian businesses — with real intelligence,
              not scripted responses.
            </motion.p>
          </motion.div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 24 }}>
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                viewport={{ once: true }}
                className="card"
                style={{ padding: '32px', cursor: 'default' }}
              >
                <div style={{
                  width: 52,
                  height: 52,
                  borderRadius: 'var(--radius-md)',
                  background: `${f.color}12`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: 20,
                }}>
                  <f.icon size={24} color={f.color} />
                </div>
                <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 10, color: 'var(--color-text)' }}>
                  {f.title}
                </h3>
                <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', lineHeight: 1.7 }}>
                  {f.desc}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== HOW IT WORKS ===== */}
      <section style={{ padding: '80px 0', background: '#fff' }}>
        <div className="container">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={stagger}
            style={{ textAlign: 'center', marginBottom: 56 }}
          >
            <motion.h2 variants={fadeInUp} className="section-title">How It Works</motion.h2>
            <motion.p variants={fadeInUp} className="section-subtitle">Three simple steps to transform your customer experience</motion.p>
          </motion.div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 40 }}>
            {[
              { step: '01', icon: Phone, title: 'Customer Calls or Chats', desc: 'Customer reaches out via phone, WhatsApp, or your website. Aurkira answers instantly in their preferred language.' },
              { step: '02', icon: Bot, title: 'AI Understands & Responds', desc: 'Our AI processes natural speech, detects intent, sentiment, and urgency. Responds with human-like conversation.' },
              { step: '03', icon: CheckCircle, title: 'Issue Resolved Instantly', desc: 'Queries are resolved in real-time. Complex issues are escalated intelligently with full context to human agents.' },
            ].map((item, i) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.15 }}
                viewport={{ once: true }}
                style={{ textAlign: 'center' }}
              >
                <div style={{
                  width: 80,
                  height: 80,
                  borderRadius: '50%',
                  background: 'var(--gradient-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 20px',
                  boxShadow: '0 8px 30px rgba(233,30,140,0.2)',
                }}>
                  <item.icon size={32} color="#fff" />
                </div>
                <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--color-primary)', letterSpacing: 1 }}>STEP {item.step}</span>
                <h3 style={{ fontSize: 20, fontWeight: 700, margin: '8px 0 12px', color: 'var(--color-text)' }}>{item.title}</h3>
                <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', lineHeight: 1.7 }}>{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== INTEGRATIONS ===== */}
      <section style={{ padding: '80px 0', background: 'var(--color-bg-soft)' }}>
        <div className="container" style={{ textAlign: 'center' }}>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="section-title"
          >
            Integrates With Everything
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            viewport={{ once: true }}
            className="section-subtitle"
          >
            Plug into your existing infrastructure in minutes
          </motion.p>

          <div style={{ display: 'flex', justifyContent: 'center', gap: 24, flexWrap: 'wrap' }}>
            {integrations.map((int, i) => (
              <motion.div
                key={int.name}
                initial={{ opacity: 0, scale: 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.08 }}
                viewport={{ once: true }}
                style={{
                  background: '#fff',
                  border: `2px solid ${int.color}20`,
                  borderRadius: 'var(--radius-lg)',
                  padding: '24px 36px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 8,
                  transition: 'all var(--transition)',
                  cursor: 'default',
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = int.color; e.currentTarget.style.boxShadow = `0 8px 24px ${int.color}20` }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = `${int.color}20`; e.currentTarget.style.boxShadow = 'none' }}
              >
                <div style={{ width: 48, height: 48, borderRadius: 12, background: `${int.color}12`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Building2 size={22} color={int.color} />
                </div>
                <span style={{ fontWeight: 700, fontSize: 14, color: 'var(--color-text)' }}>{int.name}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== CTA ===== */}
      <section style={{
        padding: '80px 0',
        background: 'var(--gradient-primary)',
        textAlign: 'center',
      }}>
        <div className="container">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 style={{
              fontFamily: 'Playfair Display, serif',
              fontSize: 'clamp(28px, 4vw, 44px)',
              color: '#fff',
              fontWeight: 700,
              marginBottom: 16,
            }}>
              Ready to Transform Your Customer Experience?
            </h2>
            <p style={{ color: 'rgba(255,255,255,0.85)', fontSize: 18, marginBottom: 36, maxWidth: 560, margin: '0 auto 36px' }}>
              Try Aurkira's AI voice assistant right now — no signup required.
              Speak in Hindi, Tamil, or any supported language.
            </p>
            <Link to="/demo" className="btn" style={{
              background: '#fff',
              color: 'var(--color-primary)',
              fontSize: 18,
              padding: '16px 40px',
              fontWeight: 700,
              boxShadow: '0 8px 30px rgba(0,0,0,0.15)',
            }}>
              <Mic size={20} /> Launch Voice Demo
            </Link>
          </motion.div>
        </div>
      </section>
    </div>
  )
}
