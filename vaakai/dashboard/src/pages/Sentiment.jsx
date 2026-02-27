import React, { useEffect, useState } from 'react';
import {
  LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend, PieChart, Pie, Cell,
} from 'recharts';
import { getSentimentTrends } from '../api';

const COLORS = {
  positive: '#10b981',
  neutral: '#6b7280',
  negative: '#ef4444',
};

const EMOTION_COLORS = ['#6C63FF', '#10b981', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6', '#ec4899', '#14b8a6', '#6b7280'];

const DEMO_TRENDS = Array.from({ length: 7 }, (_, i) => {
  const d = new Date();
  d.setDate(d.getDate() - (6 - i));
  return {
    date: d.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric' }),
    positive: 40 + Math.floor(Math.random() * 20),
    neutral: 25 + Math.floor(Math.random() * 15),
    negative: 8 + Math.floor(Math.random() * 12),
    avg_polarity: (-0.2 + Math.random() * 0.8).toFixed(2),
  };
});

const DEMO_EMOTIONS = [
  { name: 'neutral', value: 340 },
  { name: 'happy', value: 210 },
  { name: 'frustrated', value: 120 },
  { name: 'angry', value: 85 },
  { name: 'sad', value: 60 },
  { name: 'confused', value: 55 },
  { name: 'fearful', value: 30 },
  { name: 'surprised', value: 25 },
  { name: 'disgusted', value: 15 },
];

export default function Sentiment() {
  const [trends, setTrends] = useState(DEMO_TRENDS);
  const [emotions, setEmotions] = useState(DEMO_EMOTIONS);

  useEffect(() => {
    getSentimentTrends(168)
      .then((d) => {
        if (d.daily) setTrends(d.daily);
        if (d.emotions) setEmotions(d.emotions);
      })
      .catch(() => {});
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Sentiment & Emotion</h1>
        <p className="text-gray-500 mt-1">Monitor customer mood across conversations</p>
      </div>

      {/* Sentiment trend line */}
      <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">7-Day Sentiment Trend</h2>
        <ResponsiveContainer width="100%" height={320}>
          <AreaChart data={trends}>
            <defs>
              <linearGradient id="gPos" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={COLORS.positive} stopOpacity={0.15} />
                <stop offset="95%" stopColor={COLORS.positive} stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gNeg" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={COLORS.negative} stopOpacity={0.15} />
                <stop offset="95%" stopColor={COLORS.negative} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            <Area type="monotone" dataKey="positive" stroke={COLORS.positive} fill="url(#gPos)" strokeWidth={2} />
            <Area type="monotone" dataKey="neutral" stroke={COLORS.neutral} fill="none" strokeWidth={2} strokeDasharray="5 5" />
            <Area type="monotone" dataKey="negative" stroke={COLORS.negative} fill="url(#gNeg)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Polarity over time */}
        <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Avg Polarity Score</h2>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={trends}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis domain={[-1, 1]} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Line type="monotone" dataKey="avg_polarity" stroke="#6C63FF" strokeWidth={2} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Emotion distribution pie */}
        <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Emotion Distribution</h2>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={emotions}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
                dataKey="value"
                nameKey="name"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {emotions.map((_, idx) => (
                  <Cell key={idx} fill={EMOTION_COLORS[idx % EMOTION_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
