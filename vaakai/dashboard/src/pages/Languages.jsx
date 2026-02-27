import React, { useEffect, useState } from 'react';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { getLanguageDistribution } from '../api';

const COLORS = [
  '#6C63FF', '#10b981', '#f59e0b', '#ef4444', '#3b82f6',
  '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#6366f1',
  '#84cc16', '#06b6d4',
];

const LANG_NAMES = {
  hi: 'Hindi', en: 'English', bn: 'Bengali', ta: 'Tamil', te: 'Telugu',
  mr: 'Marathi', gu: 'Gujarati', kn: 'Kannada', ml: 'Malayalam', pa: 'Punjabi',
  or: 'Odia', as: 'Assamese', ur: 'Urdu', sa: 'Sanskrit', ne: 'Nepali',
  sd: 'Sindhi', ks: 'Kashmiri', doi: 'Dogri', mni: 'Manipuri', sat: 'Santali',
  mai: 'Maithili', kok: 'Konkani',
};

const DEMO_DIST = [
  { language: 'hi', calls: 420 },
  { language: 'en', calls: 380 },
  { language: 'bn', calls: 120 },
  { language: 'ta', calls: 98 },
  { language: 'te', calls: 87 },
  { language: 'mr', calls: 65 },
  { language: 'gu', calls: 42 },
  { language: 'kn', calls: 35 },
].map((d) => ({ ...d, name: LANG_NAMES[d.language] || d.language }));

export default function Languages() {
  const [data, setData] = useState(DEMO_DIST);

  useEffect(() => {
    getLanguageDistribution(720)
      .then((d) => {
        if (Array.isArray(d) && d.length) {
          setData(d.map((item) => ({ ...item, name: LANG_NAMES[item.language] || item.language })));
        }
      })
      .catch(() => {});
  }, []);

  const total = data.reduce((s, d) => s + d.calls, 0);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Language Distribution</h1>
        <p className="text-gray-500 mt-1">Breakdown of languages used across conversations</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pie chart */}
        <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Distribution</h2>
          <ResponsiveContainer width="100%" height={360}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={70}
                outerRadius={130}
                paddingAngle={2}
                dataKey="calls"
                nameKey="name"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {data.map((_, idx) => (
                  <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(v) => [v, 'Calls']} />
            </PieChart>
          </ResponsiveContainer>
          <div className="text-center text-sm text-gray-500 mt-2">Total: {total.toLocaleString()} calls</div>
        </div>

        {/* Bar chart */}
        <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Calls by Language</h2>
          <ResponsiveContainer width="100%" height={360}>
            <BarChart data={data} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis dataKey="name" type="category" width={80} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="calls" radius={[0, 4, 4, 0]}>
                {data.map((_, idx) => (
                  <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Language table */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50/50">
              <th className="text-left py-3 px-4 font-medium text-gray-500">Language</th>
              <th className="text-left py-3 px-4 font-medium text-gray-500">Code</th>
              <th className="text-left py-3 px-4 font-medium text-gray-500">Calls</th>
              <th className="text-left py-3 px-4 font-medium text-gray-500">Share</th>
              <th className="text-left py-3 px-4 font-medium text-gray-500">Bar</th>
            </tr>
          </thead>
          <tbody>
            {data.map((d, idx) => (
              <tr key={d.language} className="border-b border-gray-50">
                <td className="py-3 px-4 font-medium">{d.name}</td>
                <td className="py-3 px-4 text-gray-500 uppercase">{d.language}</td>
                <td className="py-3 px-4">{d.calls.toLocaleString()}</td>
                <td className="py-3 px-4 text-gray-500">{((d.calls / total) * 100).toFixed(1)}%</td>
                <td className="py-3 px-4 w-48">
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${(d.calls / data[0].calls) * 100}%`,
                        backgroundColor: COLORS[idx % COLORS.length],
                      }}
                    />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
