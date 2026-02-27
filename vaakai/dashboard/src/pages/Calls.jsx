import React, { useEffect, useState } from 'react';
import { Phone, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { getCallList } from '../api';

const DEMO_CALLS = Array.from({ length: 20 }, (_, i) => ({
  id: `call_${1000 + i}`,
  customer_phone: `+91 98XXX ${String(10000 + i).slice(-5)}`,
  direction: i % 3 === 0 ? 'outbound' : 'inbound',
  status: ['completed', 'completed', 'escalated', 'completed', 'abandoned'][i % 5],
  language: ['hi', 'en', 'bn', 'ta', 'te'][i % 5],
  duration_sec: 60 + Math.floor(Math.random() * 300),
  sentiment: (['positive', 'neutral', 'negative'])[i % 3],
  csat_score: (3 + Math.random() * 2).toFixed(1),
  created_at: new Date(Date.now() - i * 3600000).toISOString(),
}));

const STATUS_BADGE = {
  completed: 'bg-emerald-50 text-emerald-700',
  escalated: 'bg-amber-50 text-amber-700',
  abandoned: 'bg-red-50 text-red-700',
  active: 'bg-blue-50 text-blue-700',
};

const SENTIMENT_DOT = {
  positive: 'bg-emerald-400',
  neutral: 'bg-gray-400',
  negative: 'bg-red-400',
};

const LANG_NAMES = {
  hi: 'Hindi', en: 'English', bn: 'Bengali', ta: 'Tamil', te: 'Telugu',
  mr: 'Marathi', gu: 'Gujarati', kn: 'Kannada', ml: 'Malayalam', pa: 'Punjabi',
};

export default function Calls() {
  const [calls, setCalls] = useState(DEMO_CALLS);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    getCallList(50, 0).then((d) => d.length && setCalls(d)).catch(() => {});
  }, []);

  const filtered = filter === 'all' ? calls : calls.filter((c) => c.status === filter);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Call History</h1>
        <p className="text-gray-500 mt-1">Browse and filter recent call records</p>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {['all', 'completed', 'escalated', 'abandoned'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === f
                ? 'bg-primary text-white'
                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50/50">
              <th className="text-left py-3 px-4 font-medium text-gray-500">Call ID</th>
              <th className="text-left py-3 px-4 font-medium text-gray-500">Phone</th>
              <th className="text-left py-3 px-4 font-medium text-gray-500">Dir</th>
              <th className="text-left py-3 px-4 font-medium text-gray-500">Language</th>
              <th className="text-left py-3 px-4 font-medium text-gray-500">Duration</th>
              <th className="text-left py-3 px-4 font-medium text-gray-500">Sentiment</th>
              <th className="text-left py-3 px-4 font-medium text-gray-500">CSAT</th>
              <th className="text-left py-3 px-4 font-medium text-gray-500">Status</th>
              <th className="text-left py-3 px-4 font-medium text-gray-500">Time</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((c) => (
              <tr key={c.id} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                <td className="py-3 px-4 font-mono text-xs text-gray-600">{c.id}</td>
                <td className="py-3 px-4">{c.customer_phone}</td>
                <td className="py-3 px-4">
                  {c.direction === 'inbound' ? (
                    <ArrowDownRight className="w-4 h-4 text-blue-500" />
                  ) : (
                    <ArrowUpRight className="w-4 h-4 text-emerald-500" />
                  )}
                </td>
                <td className="py-3 px-4">{LANG_NAMES[c.language] || c.language}</td>
                <td className="py-3 px-4">{Math.floor(c.duration_sec / 60)}m {c.duration_sec % 60}s</td>
                <td className="py-3 px-4">
                  <span className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${SENTIMENT_DOT[c.sentiment] || 'bg-gray-300'}`} />
                    {c.sentiment}
                  </span>
                </td>
                <td className="py-3 px-4">{c.csat_score}</td>
                <td className="py-3 px-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_BADGE[c.status] || 'bg-gray-50 text-gray-600'}`}>
                    {c.status}
                  </span>
                </td>
                <td className="py-3 px-4 text-gray-500 text-xs">
                  {new Date(c.created_at).toLocaleTimeString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="text-center py-12 text-gray-400">No calls match the selected filter.</div>
        )}
      </div>
    </div>
  );
}
