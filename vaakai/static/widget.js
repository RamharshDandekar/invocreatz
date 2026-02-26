/**
 * VaakAI Widget SDK
 * Embeddable voice/chat widget for websites.
 * 
 * Usage:
 *   <script src="https://cdn.vaakai.com/widget.js"></script>
 *   <script>
 *     VaakAI.init({
 *       apiUrl: 'https://api.vaakai.com',
 *       position: 'bottom-right',
 *       primaryColor: '#6C63FF',
 *       language: 'hi',
 *       greeting: 'Namaste! Kaise madad kar sakta hoon?'
 *     });
 *   </script>
 */

(function (window, document) {
  'use strict';

  const DEFAULT_CONFIG = {
    apiUrl: 'http://localhost:8000',
    position: 'bottom-right',
    primaryColor: '#6C63FF',
    textColor: '#FFFFFF',
    language: 'hi',
    greeting: 'Namaste! VaakAI mein aapka swagat hai.',
    enableVoice: true,
    enableText: true,
    widgetTitle: 'VaakAI Support',
    avatarUrl: null,
  };

  let config = { ...DEFAULT_CONFIG };
  let sessionId = null;
  let ws = null;
  let isOpen = false;
  let isRecording = false;
  let mediaRecorder = null;
  let audioChunks = [];

  // ── Widget HTML ────────────────────────────

  function createWidget() {
    const container = document.createElement('div');
    container.id = 'vaakai-widget';
    container.innerHTML = `
      <style>
        #vaakai-widget {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          position: fixed;
          z-index: 99999;
        }
        #vaakai-widget * { box-sizing: border-box; margin: 0; padding: 0; }
        
        .vaakai-fab {
          width: 60px; height: 60px;
          border-radius: 50%;
          background: ${config.primaryColor};
          color: ${config.textColor};
          border: none;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 4px 16px rgba(0,0,0,0.2);
          transition: transform 0.2s;
          position: fixed;
          ${config.position.includes('right') ? 'right: 24px;' : 'left: 24px;'}
          ${config.position.includes('bottom') ? 'bottom: 24px;' : 'top: 24px;'}
        }
        .vaakai-fab:hover { transform: scale(1.1); }
        .vaakai-fab svg { width: 28px; height: 28px; fill: currentColor; }
        
        .vaakai-panel {
          display: none;
          position: fixed;
          ${config.position.includes('right') ? 'right: 24px;' : 'left: 24px;'}
          ${config.position.includes('bottom') ? 'bottom: 96px;' : 'top: 96px;'}
          width: 380px;
          height: 520px;
          background: #fff;
          border-radius: 16px;
          box-shadow: 0 8px 32px rgba(0,0,0,0.15);
          overflow: hidden;
          flex-direction: column;
        }
        .vaakai-panel.open { display: flex; }
        
        .vaakai-header {
          background: ${config.primaryColor};
          color: ${config.textColor};
          padding: 16px 20px;
          font-size: 16px;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .vaakai-header .status-dot {
          width: 8px; height: 8px;
          background: #4ade80;
          border-radius: 50%;
        }
        
        .vaakai-messages {
          flex: 1;
          overflow-y: auto;
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        
        .vaakai-msg {
          max-width: 85%;
          padding: 10px 14px;
          border-radius: 12px;
          font-size: 14px;
          line-height: 1.4;
          word-wrap: break-word;
        }
        .vaakai-msg.bot {
          background: #f1f1f4;
          align-self: flex-start;
          border-bottom-left-radius: 4px;
        }
        .vaakai-msg.user {
          background: ${config.primaryColor};
          color: ${config.textColor};
          align-self: flex-end;
          border-bottom-right-radius: 4px;
        }
        .vaakai-msg .meta {
          font-size: 11px;
          opacity: 0.6;
          margin-top: 4px;
        }
        
        .vaakai-input-area {
          padding: 12px 16px;
          border-top: 1px solid #eee;
          display: flex;
          gap: 8px;
          align-items: center;
        }
        .vaakai-input-area input {
          flex: 1;
          border: 1px solid #ddd;
          border-radius: 20px;
          padding: 8px 16px;
          font-size: 14px;
          outline: none;
        }
        .vaakai-input-area input:focus { border-color: ${config.primaryColor}; }
        
        .vaakai-btn {
          width: 40px; height: 40px;
          border-radius: 50%;
          border: none;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background 0.2s;
        }
        .vaakai-btn-send {
          background: ${config.primaryColor};
          color: ${config.textColor};
        }
        .vaakai-btn-mic {
          background: ${isRecording ? '#ef4444' : '#f1f1f4'};
          color: ${isRecording ? '#fff' : '#333'};
        }
        .vaakai-btn-mic.recording { background: #ef4444; color: #fff; }
        
        .vaakai-typing {
          display: none;
          padding: 8px 14px;
          align-self: flex-start;
        }
        .vaakai-typing span {
          display: inline-block;
          width: 6px; height: 6px;
          background: #999;
          border-radius: 50%;
          margin: 0 2px;
          animation: vaakaiDot 1.4s infinite;
        }
        .vaakai-typing span:nth-child(2) { animation-delay: 0.2s; }
        .vaakai-typing span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes vaakaiDot {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
          40% { transform: scale(1); opacity: 1; }
        }
      </style>
      
      <button class="vaakai-fab" id="vaakai-fab" aria-label="Open VaakAI Chat">
        <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>
      </button>
      
      <div class="vaakai-panel" id="vaakai-panel">
        <div class="vaakai-header">
          <span class="status-dot"></span>
          <span>${config.widgetTitle}</span>
        </div>
        
        <div class="vaakai-messages" id="vaakai-messages">
          <div class="vaakai-msg bot">${config.greeting}</div>
        </div>
        
        <div class="vaakai-typing" id="vaakai-typing">
          <span></span><span></span><span></span>
        </div>
        
        <div class="vaakai-input-area">
          ${config.enableVoice ? `
            <button class="vaakai-btn vaakai-btn-mic" id="vaakai-mic" aria-label="Voice input">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5zm6 6c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
              </svg>
            </button>
          ` : ''}
          
          ${config.enableText ? `
            <input type="text" id="vaakai-input" placeholder="Type a message..." autocomplete="off" />
            <button class="vaakai-btn vaakai-btn-send" id="vaakai-send" aria-label="Send">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
              </svg>
            </button>
          ` : ''}
        </div>
      </div>
    `;

    document.body.appendChild(container);
    bindEvents();
  }

  // ── Events ──────────────────────────────────

  function bindEvents() {
    document.getElementById('vaakai-fab').addEventListener('click', togglePanel);

    if (config.enableText) {
      document.getElementById('vaakai-send').addEventListener('click', sendTextMessage);
      document.getElementById('vaakai-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendTextMessage();
      });
    }

    if (config.enableVoice) {
      document.getElementById('vaakai-mic').addEventListener('click', toggleRecording);
    }
  }

  function togglePanel() {
    isOpen = !isOpen;
    const panel = document.getElementById('vaakai-panel');
    panel.classList.toggle('open', isOpen);

    if (isOpen && !sessionId) {
      initSession();
    }
  }

  // ── Session Management ─────────────────────

  async function initSession() {
    try {
      const formData = new FormData();
      formData.append('phone_number', 'widget_' + Date.now());
      formData.append('channel', 'widget');

      const resp = await fetch(`${config.apiUrl}/api/v1/call/initiate`, {
        method: 'POST',
        body: formData,
      });

      const data = await resp.json();
      sessionId = data.session_id;

      // Connect WebSocket
      const wsUrl = config.apiUrl.replace('http', 'ws');
      ws = new WebSocket(`${wsUrl}/api/v1/call/ws/${sessionId}`);

      ws.onmessage = handleWSMessage;
      ws.onclose = () => {
        sessionId = null;
        ws = null;
      };
    } catch (e) {
      console.error('VaakAI: Session init failed', e);
      addMessage('bot', 'Connection failed. Please try again.');
    }
  }

  function handleWSMessage(event) {
    if (typeof event.data === 'string') {
      const msg = JSON.parse(event.data);

      if (msg.type === 'response' && msg.text) {
        hideTyping();
        addMessage('bot', msg.text, msg.latency_ms ? `${msg.latency_ms}ms` : null);
      } else if (msg.type === 'transcript' && msg.text) {
        addMessage('user', msg.text);
      } else if (msg.type === 'backchannel' && msg.text) {
        addMessage('bot', msg.text);
      } else if (msg.type === 'escalated') {
        addMessage('bot', 'Connecting you to a human agent...');
      }
    } else if (event.data instanceof Blob) {
      // Audio response — play it
      playAudio(event.data);
    }
  }

  // ── Text Chat ──────────────────────────────

  function sendTextMessage() {
    const input = document.getElementById('vaakai-input');
    const text = input.value.trim();
    if (!text) return;

    addMessage('user', text);
    input.value = '';
    showTyping();

    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'text', text }));
    } else {
      // Fallback to REST
      sendTextREST(text);
    }
  }

  async function sendTextREST(text) {
    if (!sessionId) return;

    try {
      const formData = new FormData();
      formData.append('text', text);

      const resp = await fetch(
        `${config.apiUrl}/api/v1/call/${sessionId}/text`,
        { method: 'POST', body: formData }
      );

      const data = await resp.json();
      hideTyping();

      if (data.bot_response) {
        addMessage('bot', data.bot_response);
      }
    } catch (e) {
      hideTyping();
      addMessage('bot', 'Sorry, something went wrong.');
    }
  }

  // ── Voice Recording ────────────────────────

  async function toggleRecording() {
    if (isRecording) {
      stopRecording();
    } else {
      await startRecording();
    }
  }

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      audioChunks = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunks.push(e.data);
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });

        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(audioBlob);
        } else {
          sendAudioREST(audioBlob);
        }

        stream.getTracks().forEach(t => t.stop());
        showTyping();
      };

      mediaRecorder.start();
      isRecording = true;
      updateMicButton();
    } catch (e) {
      console.error('VaakAI: Mic access denied', e);
      addMessage('bot', 'Microphone access is required for voice input.');
    }
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
    }
    isRecording = false;
    updateMicButton();
  }

  async function sendAudioREST(blob) {
    if (!sessionId) return;

    const formData = new FormData();
    formData.append('audio', blob, 'recording.webm');

    try {
      const resp = await fetch(
        `${config.apiUrl}/api/v1/call/${sessionId}/audio`,
        { method: 'POST', body: formData }
      );
      const data = await resp.json();
      hideTyping();

      if (data.user_text) addMessage('user', data.user_text);
      if (data.bot_response) addMessage('bot', data.bot_response);
    } catch (e) {
      hideTyping();
      addMessage('bot', 'Sorry, audio processing failed.');
    }
  }

  function updateMicButton() {
    const btn = document.getElementById('vaakai-mic');
    if (btn) {
      btn.classList.toggle('recording', isRecording);
    }
  }

  // ── Audio Playback ─────────────────────────

  function playAudio(blob) {
    const audio = new Audio(URL.createObjectURL(blob));
    audio.play().catch(() => {});
  }

  // ── UI Helpers ─────────────────────────────

  function addMessage(type, text, meta) {
    const container = document.getElementById('vaakai-messages');
    const div = document.createElement('div');
    div.className = `vaakai-msg ${type}`;
    div.textContent = text;

    if (meta) {
      const metaEl = document.createElement('div');
      metaEl.className = 'meta';
      metaEl.textContent = meta;
      div.appendChild(metaEl);
    }

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  }

  function showTyping() {
    const el = document.getElementById('vaakai-typing');
    if (el) el.style.display = 'block';
  }

  function hideTyping() {
    const el = document.getElementById('vaakai-typing');
    if (el) el.style.display = 'none';
  }

  // ── Public API ─────────────────────────────

  window.VaakAI = {
    init(userConfig) {
      config = { ...DEFAULT_CONFIG, ...userConfig };

      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createWidget);
      } else {
        createWidget();
      }
    },

    open() { if (!isOpen) togglePanel(); },
    close() { if (isOpen) togglePanel(); },

    sendMessage(text) {
      if (sessionId) {
        addMessage('user', text);
        showTyping();
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'text', text }));
        } else {
          sendTextREST(text);
        }
      }
    },

    setLanguage(lang) { config.language = lang; },

    destroy() {
      if (ws) {
        ws.send(JSON.stringify({ type: 'end' }));
        ws.close();
      }
      const el = document.getElementById('vaakai-widget');
      if (el) el.remove();
    },
  };

})(window, document);
