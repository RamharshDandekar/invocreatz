import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Overview from './pages/Overview';
import Calls from './pages/Calls';
import Sentiment from './pages/Sentiment';
import Languages from './pages/Languages';
import Fraud from './pages/Fraud';
import SettingsPage from './pages/Settings';

export default function App() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 ml-64 p-8">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/calls" element={<Calls />} />
          <Route path="/sentiment" element={<Sentiment />} />
          <Route path="/languages" element={<Languages />} />
          <Route path="/fraud" element={<Fraud />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}
