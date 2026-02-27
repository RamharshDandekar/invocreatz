import React, { useEffect, useState } from 'react';
import { Save, RefreshCw, Server, Database, Shield, Globe } from 'lucide-react';
import { getHealth, getActiveSessions } from '../api';

export default function SettingsPage() {
  const [health, setHealth] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth({ status: 'unknown' }));
    getActiveSessions().then(setSessions).catch(() => {});
  }, []);

  const refresh = () => {
    getHealth().then(setHealth).catch(() => {});
    getActiveSessions().then(setSessions).catch(() => {});
  };

  return (
    <div className="space-y-8 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-500 mt-1">System status and configuration</p>
        </div>
        <button
          onClick={refresh}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
        >
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {/* System Health */}
      <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <Server className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-semibold text-gray-900">System Health</h2>
        </div>
        {health ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <HealthItem label="API Status" value={health.status} ok={health.status === 'healthy'} />
            <HealthItem label="Redis" value={health.redis || '—'} ok={health.redis === 'connected'} />
            <HealthItem label="PostgreSQL" value={health.postgres || '—'} ok={health.postgres === 'connected'} />
            <HealthItem label="Uptime" value={health.uptime || '—'} ok />
          </div>
        ) : (
          <p className="text-gray-400 text-sm">Loading health status...</p>
        )}
      </div>

      {/* Active Sessions */}
      <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <Globe className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-semibold text-gray-900">Active Sessions</h2>
          <span className="ml-auto text-sm text-gray-400">{sessions.length} active</span>
        </div>
        {sessions.length > 0 ? (
          <div className="space-y-2">
            {sessions.map((s, i) => (
              <div key={i} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg text-sm">
                <span className="font-mono text-gray-600">{s.session_id || s.id}</span>
                <span className="text-gray-500">{s.language || '—'}</span>
                <span className="text-gray-500">{s.channel || '—'}</span>
                <span className="text-gray-400 text-xs">{s.duration || '—'}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-400 text-sm">No active sessions</p>
        )}
      </div>

      {/* Configuration */}
      <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <Shield className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-semibold text-gray-900">DPDPA Compliance</h2>
        </div>
        <div className="space-y-4 text-sm">
          <ConfigRow label="PII Redaction" value="Enabled" status="active" />
          <ConfigRow label="Consent Management" value="Active" status="active" />
          <ConfigRow label="Data Retention" value="90 days" status="active" />
          <ConfigRow label="Right to Erasure" value="Supported" status="active" />
          <ConfigRow label="Audit Logging" value="Enabled" status="active" />
        </div>
      </div>

      {/* Integration Status */}
      <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <Database className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-semibold text-gray-900">Integrations</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          <IntegrationCard name="AI4Bharat STT" desc="22 Indian languages" />
          <IntegrationCard name="Deepgram Nova-3" desc="English fallback" />
          <IntegrationCard name="ElevenLabs TTS" desc="English voice synthesis" />
          <IntegrationCard name="AI4Bharat TTS" desc="14 Indian languages" />
          <IntegrationCard name="OpenAI GPT-4o" desc="Primary LLM" />
          <IntegrationCard name="Ollama / Llama 3.1" desc="Local LLM fallback" />
          <IntegrationCard name="Salesforce CRM" desc="Customer management" />
          <IntegrationCard name="SAP ERP" desc="Order & inventory" />
          <IntegrationCard name="WhatsApp Cloud" desc="Meta Business API" />
          <IntegrationCard name="LiveKit" desc="WebRTC streaming" />
        </div>
      </div>
    </div>
  );
}

function HealthItem({ label, value, ok }) {
  return (
    <div className="p-3 bg-gray-50 rounded-lg">
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`mt-1 font-semibold ${ok ? 'text-emerald-600' : 'text-red-500'}`}>{value}</p>
    </div>
  );
}

function ConfigRow({ label, value, status }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
      <span className="text-gray-600">{label}</span>
      <div className="flex items-center gap-2">
        <span className="text-gray-900 font-medium">{value}</span>
        <span className={`w-2 h-2 rounded-full ${status === 'active' ? 'bg-emerald-400' : 'bg-gray-300'}`} />
      </div>
    </div>
  );
}

function IntegrationCard({ name, desc }) {
  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
      <div className="w-2 h-2 rounded-full bg-emerald-400" />
      <div>
        <p className="font-medium text-gray-900">{name}</p>
        <p className="text-xs text-gray-500">{desc}</p>
      </div>
    </div>
  );
}
