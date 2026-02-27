import React, { useEffect, useState } from 'react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { Phone, Clock, Star, Users } from 'lucide-react';
import StatCard from '../components/StatCard';
import { getAnalyticsSummary, getPerformanceMetrics, getTopIntents } from '../api';

// Demo data used when API is unavailable
const DEMO_SUMMARY = {
  total_calls: 1247,
  avg_duration: 185,
  avg_csat: 4.3,
  active_sessions: 12,
  resolution_rate: 0.87,
  escalation_rate: 0.08,
};

const DEMO_HOURLY = Array.from({ length: 24 }, (_, i) => ({
  hour: `${String(i).padStart(2, '0')}:00`,
  calls: Math.floor(30 + Math.random() * 70),
  avg_latency_ms: Math.floor(180 + Math.random() * 120),
}));

const DEMO_INTENTS = [
  { intent: 'order_status', count: 312 },
  { intent: 'billing_inquiry', count: 198 },
  { intent: 'complaint', count: 167 },
  { intent: 'refund_request', count: 145 },
  { intent: 'product_info', count: 112 },
  { intent: 'shipping_query', count: 98 },
  { intent: 'account_update', count: 76 },
  { intent: 'escalation', count: 54 },
];

export default function Overview() {
  const [summary, setSummary] = useState(DEMO_SUMMARY);
  const [hourly, setHourly] = useState(DEMO_HOURLY);
  const [intents, setIntents] = useState(DEMO_INTENTS);

  useEffect(() => {
    getAnalyticsSummary(24).then(setSummary).catch(() => {});
    getPerformanceMetrics(24)
      .then((d) => d.hourly && setHourly(d.hourly))
      .catch(() => {});
    getTopIntents(8).then(setIntents).catch(() => {});
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard Overview</h1>
        <p className="text-gray-500 mt-1">Real-time analytics for VaakAI voice operations</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Calls (24h)"
          value={summary.total_calls?.toLocaleString() ?? '—'}
          icon={Phone}
          color="primary"
          subtitle={`${(summary.resolution_rate * 100).toFixed(0)}% resolved`}
        />
        <StatCard
          title="Avg Duration"
          value={`${Math.floor((summary.avg_duration || 0) / 60)}m ${(summary.avg_duration || 0) % 60}s`}
          icon={Clock}
          color="blue"
        />
        <StatCard
          title="Avg CSAT"
          value={(summary.avg_csat || 0).toFixed(1)}
          icon={Star}
          color="green"
          subtitle="out of 5.0"
        />
        <StatCard
          title="Active Sessions"
          value={summary.active_sessions ?? 0}
          icon={Users}
          color="amber"
          subtitle={`${(summary.escalation_rate * 100).toFixed(1)}% escalation`}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hourly Call Volume */}
        <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Hourly Call Volume</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={hourly}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="hour" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="calls" fill="#6C63FF" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Response Latency */}
        <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Avg Response Latency</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={hourly}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="hour" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} unit="ms" />
              <Tooltip />
              <Line type="monotone" dataKey="avg_latency_ms" stroke="#6C63FF" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Intents */}
      <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Intents</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={intents} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis dataKey="intent" type="category" width={130} tick={{ fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey="count" fill="#6C63FF" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
