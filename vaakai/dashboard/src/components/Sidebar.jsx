import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Phone,
  Heart,
  Globe,
  ShieldAlert,
  Settings,
  Mic,
} from 'lucide-react';

const links = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/calls', label: 'Calls', icon: Phone },
  { to: '/sentiment', label: 'Sentiment', icon: Heart },
  { to: '/languages', label: 'Languages', icon: Globe },
  { to: '/fraud', label: 'Fraud Alerts', icon: ShieldAlert },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 w-64 bg-white border-r border-gray-100 flex flex-col z-30">
      {/* Brand */}
      <div className="h-16 flex items-center gap-3 px-6 border-b border-gray-100">
        <div className="p-2 bg-primary rounded-lg">
          <Mic className="w-5 h-5 text-white" />
        </div>
        <span className="text-xl font-bold text-gray-900">VaakAI</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary/10 text-primary'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`
            }
          >
            <Icon className="w-5 h-5" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-100">
        <div className="text-xs text-gray-400 text-center">
          VaakAI v1.0 &middot; DPDPA Compliant
        </div>
      </div>
    </aside>
  );
}
