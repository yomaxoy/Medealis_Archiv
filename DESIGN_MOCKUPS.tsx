"""
USER VIEW REDESIGN MOCKUPS
TypeScript/React Implementation Concepts

This file contains 5 different design approaches for modernizing the User View
from Streamlit to a professional TypeScript/React frontend.

Each approach demonstrates:
- Component architecture
- Type safety with TypeScript
- Modern UI/UX patterns
- Warehouse-specific optimizations
"""

// ============================================================================
// MOCKUP 1: MINIMALIST WAREHOUSE WORKER UI
// Focus: Speed, Simplicity, Large Touch Targets
// Best for: Warehouse workers with gloves, mobile/tablet
// ============================================================================

import React, { useState } from 'react';
import { Search, Plus, BarChart3, Clock } from 'lucide-react';

interface WareouseItem {
  id: string;
  delivery_number: string;
  article_number: string;
  batch_number: string;
  quantity: number;
  status: 'Daten geprüft' | 'Dokumente geprüft' | 'Vermessen' | 'Abgeschlossen';
  timestamp: Date;
}

export const MinimalistUI: React.FC = () => {
  const [items, setItems] = useState<WareouseItem[]>([]);
  const [filter, setFilter] = useState('');
  const [scanning, setScanning] = useState(false);

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* HEADER: Minimal, Large Touch Targets */}
      <div className="bg-blue-600 text-white p-6 shadow-lg">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">📦 Wareneingangskontrolle</h1>
            <p className="text-blue-100 mt-2">Goods Receipt Control</p>
          </div>
          <button className="text-sm text-blue-100">
            👤 {/* User menu - small */}
          </button>
        </div>
      </div>

      {/* ACTION BUTTONS: Large, Finger-friendly */}
      <div className="bg-gray-50 border-b border-gray-200 p-6">
        <div className="max-w-6xl mx-auto grid grid-cols-2 gap-4 sm:grid-cols-4">
          {/* Primary Action */}
          <button className="bg-green-500 hover:bg-green-600 text-white font-bold py-6 px-4 rounded-lg text-lg flex flex-col items-center gap-2 transition-colors shadow-md">
            <span className="text-3xl">📄</span>
            <span>Lieferschein Scannen</span>
          </button>

          {/* Secondary Actions */}
          <button className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-6 px-4 rounded-lg text-lg flex flex-col items-center gap-2 transition-colors shadow-md">
            <span className="text-3xl">➕</span>
            <span>Neue Lieferung</span>
          </button>

          <button className="bg-gray-400 hover:bg-gray-500 text-white font-bold py-6 px-4 rounded-lg text-lg flex flex-col items-center gap-2 transition-colors shadow-md">
            <span className="text-3xl">🔍</span>
            <span>Suchen</span>
          </button>

          <button className="bg-gray-400 hover:bg-gray-500 text-white font-bold py-6 px-4 rounded-lg text-lg flex flex-col items-center gap-2 transition-colors shadow-md">
            <span className="text-3xl">🔄</span>
            <span>Aktualisieren</span>
          </button>
        </div>
      </div>

      {/* SEARCH BAR: Simple, Large Input */}
      <div className="bg-white border-b border-gray-200 p-6">
        <div className="max-w-6xl mx-auto">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Lieferschein-Nr oder Artikel-Nr eingeben..."
              className="w-full pl-12 pr-4 py-4 text-lg border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* ITEM TABLE: Large Cards, Optimized for Touch */}
      <div className="flex-1 bg-gray-50 p-6 overflow-auto">
        <div className="max-w-6xl mx-auto space-y-4">
          {items.length === 0 ? (
            <div className="bg-white p-12 rounded-lg border-2 border-dashed border-gray-300 text-center">
              <p className="text-gray-500 text-xl">Noch keine Lieferungen</p>
              <p className="text-gray-400">Klicken Sie oben auf "Lieferschein Scannen" zum Starten</p>
            </div>
          ) : (
            items.map((item) => (
              <div
                key={item.id}
                className="bg-white p-6 rounded-lg shadow-md border-l-4 border-blue-500 hover:shadow-lg transition-shadow"
              >
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-4">
                  <div>
                    <p className="text-gray-500 text-sm">Lieferschein</p>
                    <p className="text-2xl font-bold">{item.delivery_number}</p>
                  </div>
                  <div>
                    <p className="text-gray-500 text-sm">Artikel</p>
                    <p className="text-2xl font-bold">{item.article_number}</p>
                  </div>
                </div>

                {/* Status Badge */}
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <span className="inline-block bg-blue-100 text-blue-800 px-4 py-2 rounded-full text-sm font-bold">
                      {item.status}
                    </span>
                  </div>
                  <span className="text-gray-400 text-sm">{item.timestamp.toLocaleString()}</span>
                </div>

                {/* Actions: Large Buttons */}
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                  <button className="bg-blue-500 text-white font-bold py-3 rounded-lg hover:bg-blue-600 transition-colors">
                    ✏️ Bearbeiten
                  </button>
                  <button className="bg-green-500 text-white font-bold py-3 rounded-lg hover:bg-green-600 transition-colors">
                    ✓ Bestätigen
                  </button>
                  <button className="bg-orange-500 text-white font-bold py-3 rounded-lg hover:bg-orange-600 transition-colors">
                    📋 Details
                  </button>
                  <button className="bg-red-500 text-white font-bold py-3 rounded-lg hover:bg-red-600 transition-colors">
                    🗑️ Löschen
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* FOOTER: Status & Info */}
      <div className="bg-gray-800 text-white p-4 text-center text-sm">
        <p>✅ System bereit | 📡 Online | 🔋 Akku: 85%</p>
      </div>
    </div>
  );
};

// ============================================================================
// MOCKUP 2: PROFESSIONAL ENTERPRISE UI
// Focus: Advanced features, data density, admin-friendly
// Best for: Professional environments, desktop/large screens
// ============================================================================

export const ProfessionalEnterpriseUI: React.FC = () => {
  const [selectedView, setSelectedView] = useState<'list' | 'grid' | 'kanban'>('list');
  const [sortBy, setSortBy] = useState<'date' | 'status' | 'article'>('date');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      {/* TOP NAVIGATION: Professional Header */}
      <header className="bg-gradient-to-r from-slate-800 to-slate-900 border-b border-slate-700 shadow-2xl">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-xl font-bold">📦</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Warehouse Management System</h1>
              <p className="text-sm text-slate-400">Goods Receipt Control Dashboard</p>
            </div>
          </div>

          {/* Top Right: User & Status */}
          <div className="flex items-center gap-6">
            <div className="text-right">
              <p className="text-sm font-medium">John Müller</p>
              <p className="text-xs text-slate-400">Warehouse Operator</p>
            </div>
            <div className="w-10 h-10 bg-gradient-to-br from-green-400 to-green-600 rounded-full" />
          </div>
        </div>
      </header>

      {/* MAIN CONTENT */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* TOOLBAR: Advanced Controls */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 mb-6 shadow-xl">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            {/* Filter Input */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Search</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Delivery, Article, Batch..."
                  className="w-full pl-10 pr-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:border-blue-500 focus:outline-none text-white placeholder-slate-400"
                />
              </div>
            </div>

            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Status</label>
              <select className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:border-blue-500 focus:outline-none text-white">
                <option>Alle</option>
                <option>Daten geprüft</option>
                <option>Dokumente geprüft</option>
                <option>Vermessen</option>
              </select>
            </div>

            {/* Date Range */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Date Range</label>
              <select className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:border-blue-500 focus:outline-none text-white">
                <option>Heute</option>
                <option>Diese Woche</option>
                <option>Dieser Monat</option>
              </select>
            </div>

            {/* Sort By */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Sort By</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:border-blue-500 focus:outline-none text-white"
              >
                <option value="date">Neueste zuerst</option>
                <option value="status">Nach Status</option>
                <option value="article">Nach Artikel</option>
              </select>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 flex-wrap">
            <button className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white font-bold py-2 px-6 rounded-lg transition-all shadow-lg">
              + Scan Delivery
            </button>
            <button className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-bold py-2 px-6 rounded-lg transition-all shadow-lg">
              + New Delivery
            </button>
            <button className="bg-slate-700 hover:bg-slate-600 text-white font-bold py-2 px-6 rounded-lg transition-all border border-slate-600">
              Export CSV
            </button>
            <button className="bg-slate-700 hover:bg-slate-600 text-white font-bold py-2 px-6 rounded-lg transition-all border border-slate-600">
              Print Report
            </button>
          </div>
        </div>

        {/* VIEW TOGGLE */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setSelectedView('list')}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${
              selectedView === 'list'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            📋 List View
          </button>
          <button
            onClick={() => setSelectedView('grid')}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${
              selectedView === 'grid'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            📊 Grid View
          </button>
          <button
            onClick={() => setSelectedView('kanban')}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${
              selectedView === 'kanban'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            🎯 Kanban Board
          </button>
        </div>

        {/* DATA TABLE */}
        {selectedView === 'list' && (
          <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden shadow-xl">
            {/* Table Header */}
            <div className="grid grid-cols-12 gap-4 bg-slate-900 px-6 py-4 border-b border-slate-700 font-bold text-slate-300 text-sm">
              <div className="col-span-2">Delivery</div>
              <div className="col-span-2">Article</div>
              <div className="col-span-2">Batch</div>
              <div className="col-span-2">Status</div>
              <div className="col-span-2">Timestamp</div>
              <div className="col-span-2">Actions</div>
            </div>

            {/* Table Rows */}
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="grid grid-cols-12 gap-4 px-6 py-4 border-b border-slate-700 hover:bg-slate-700 transition-colors text-sm items-center"
              >
                <div className="col-span-2 font-mono text-blue-400">LS-2024-001{i}</div>
                <div className="col-span-2 font-mono">ART-1234{i}</div>
                <div className="col-span-2 font-mono">BATCH-2024{i}</div>
                <div className="col-span-2">
                  <span className="inline-block bg-green-900 text-green-200 px-3 py-1 rounded-full text-xs font-bold">
                    Dokumente geprüft
                  </span>
                </div>
                <div className="col-span-2 text-slate-400">2024-04-29 14:3{i}</div>
                <div className="col-span-2 flex gap-2">
                  <button className="text-blue-400 hover:text-blue-300 text-xs font-bold">View</button>
                  <button className="text-yellow-400 hover:text-yellow-300 text-xs font-bold">Edit</button>
                  <button className="text-red-400 hover:text-red-300 text-xs font-bold">Delete</button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* KANBAN BOARD VIEW */}
        {selectedView === 'kanban' && (
          <div className="grid grid-cols-4 gap-6">
            {['Daten geprüft', 'Dokumente geprüft', 'Vermessen', 'Abgeschlossen'].map((status) => (
              <div key={status} className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden shadow-xl">
                <div className="bg-slate-900 px-4 py-3 border-b border-slate-700">
                  <p className="font-bold text-sm text-slate-300">{status}</p>
                  <p className="text-xs text-slate-500 mt-1">5 items</p>
                </div>
                <div className="p-4 space-y-3 max-h-96 overflow-auto">
                  {[1, 2, 3].map((item) => (
                    <div
                      key={item}
                      className="bg-slate-700 border border-slate-600 p-3 rounded-lg hover:bg-slate-600 transition-colors cursor-move"
                    >
                      <p className="font-mono text-blue-400 text-sm">LS-2024-00{item}</p>
                      <p className="text-xs text-slate-400 mt-1">ART-1234{item}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* FOOTER STATS */}
        <div className="grid grid-cols-4 gap-6 mt-8">
          {[
            { label: 'Total Items', value: '245', icon: '📦', color: 'blue' },
            { label: 'In Progress', value: '42', icon: '⏳', color: 'yellow' },
            { label: 'Completed', value: '198', icon: '✅', color: 'green' },
            { label: 'Issues', value: '5', icon: '⚠️', color: 'red' },
          ].map((stat) => (
            <div key={stat.label} className="bg-slate-800 border border-slate-700 p-4 rounded-xl text-center">
              <p className="text-3xl mb-2">{stat.icon}</p>
              <p className="text-2xl font-bold text-white">{stat.value}</p>
              <p className="text-sm text-slate-400">{stat.label}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// MOCKUP 3: MOBILE-FIRST TABLET OPTIMIZED UI
// Focus: Responsive, touch-friendly, offline-capable
// Best for: Tablets & mobile devices in warehouse
// ============================================================================

export const MobileFirstUI: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<'scan' | 'list' | 'map'>('list');

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* MOBILE HEADER */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-md mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-lg font-bold text-gray-900">WMS</h1>
          <div className="flex gap-3">
            <button className="text-sm text-gray-500">🔔</button>
            <button className="text-sm text-gray-500">⚙️</button>
          </div>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="flex-1 max-w-md mx-auto w-full px-4 py-4 space-y-4">
        {/* Quick Actions */}
        <div className="grid grid-cols-3 gap-2">
          <button className="bg-green-500 text-white p-4 rounded-lg flex flex-col items-center justify-center text-center gap-2">
            <span className="text-2xl">📄</span>
            <span className="text-xs font-bold">Scan</span>
          </button>
          <button className="bg-blue-500 text-white p-4 rounded-lg flex flex-col items-center justify-center text-center gap-2">
            <span className="text-2xl">➕</span>
            <span className="text-xs font-bold">New</span>
          </button>
          <button className="bg-gray-500 text-white p-4 rounded-lg flex flex-col items-center justify-center text-center gap-2">
            <span className="text-2xl">🔄</span>
            <span className="text-xs font-bold">Refresh</span>
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg"
          />
        </div>

        {/* Item Cards */}
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <p className="text-sm font-bold text-gray-900">LS-2024-001{i}</p>
                  <p className="text-xs text-gray-500">ART-1234{i}</p>
                </div>
                <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">OK</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <button className="bg-blue-500 text-white text-xs font-bold py-2 rounded">View</button>
                <button className="bg-green-500 text-white text-xs font-bold py-2 rounded">✓ Confirm</button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* BOTTOM NAVIGATION */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg">
        <div className="max-w-md mx-auto grid grid-cols-3">
          <button
            onClick={() => setCurrentTab('scan')}
            className={`py-4 flex flex-col items-center justify-center gap-1 text-xs font-bold ${
              currentTab === 'scan'
                ? 'text-blue-600 border-t-2 border-blue-600'
                : 'text-gray-600'
            }`}
          >
            <span className="text-lg">📄</span>
            Scan
          </button>
          <button
            onClick={() => setCurrentTab('list')}
            className={`py-4 flex flex-col items-center justify-center gap-1 text-xs font-bold ${
              currentTab === 'list'
                ? 'text-blue-600 border-t-2 border-blue-600'
                : 'text-gray-600'
            }`}
          >
            <span className="text-lg">📋</span>
            List
          </button>
          <button
            onClick={() => setCurrentTab('map')}
            className={`py-4 flex flex-col items-center justify-center gap-1 text-xs font-bold ${
              currentTab === 'map'
                ? 'text-blue-600 border-t-2 border-blue-600'
                : 'text-gray-600'
            }`}
          >
            <span className="text-lg">📍</span>
            Map
          </button>
        </div>
      </nav>
    </div>
  );
};

// ============================================================================
// MOCKUP 4: DARK MODE WAREHOUSE UI
// Focus: Eye-friendly in low-light, high contrast for visibility
// Best for: Warehouse with dim/variable lighting
// ============================================================================

export const DarkModeWarehouseUI: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* HEADER */}
      <div className="bg-gradient-to-r from-gray-900 to-gray-800 border-b-2 border-yellow-400 p-6">
        <h1 className="text-4xl font-black text-yellow-400">⚠️ WAREHOUSE CONTROL</h1>
        <p className="text-gray-400 mt-2">High-Contrast Mode for Low-Light Environments</p>
      </div>

      <div className="max-w-6xl mx-auto p-6">
        {/* BIG ACTION BUTTONS */}
        <div className="grid grid-cols-2 gap-6 mb-8">
          <button className="bg-yellow-400 hover:bg-yellow-300 text-gray-950 font-black py-8 px-6 rounded-xl text-2xl flex items-center justify-center gap-3 shadow-2xl transform hover:scale-105 transition-all">
            <span className="text-4xl">📄</span>
            SCAN DELIVERY
          </button>

          <button className="bg-green-500 hover:bg-green-400 text-gray-950 font-black py-8 px-6 rounded-xl text-2xl flex items-center justify-center gap-3 shadow-2xl transform hover:scale-105 transition-all">
            <span className="text-4xl">✅</span>
            CONFIRM ITEM
          </button>
        </div>

        {/* HIGH CONTRAST TABLE */}
        <div className="bg-gray-900 border-4 border-yellow-400 rounded-xl overflow-hidden">
          <div className="grid grid-cols-5 gap-4 bg-gray-800 px-6 py-4 border-b-4 border-yellow-400 font-black text-yellow-400 text-lg">
            <div>DELIVERY</div>
            <div>ARTICLE</div>
            <div>STATUS</div>
            <div>QTY</div>
            <div>ACTION</div>
          </div>

          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="grid grid-cols-5 gap-4 px-6 py-6 border-b border-gray-700 items-center hover:bg-gray-800 transition-colors bg-gray-900"
            >
              <div className="font-mono text-yellow-400 text-xl font-black">LS-001{i}</div>
              <div className="font-mono text-white text-lg">ART-1234{i}</div>
              <div className="font-black text-green-400 text-lg">✅ OK</div>
              <div className="font-black text-white text-lg">50</div>
              <button className="bg-yellow-400 text-gray-950 font-black py-2 px-4 rounded-lg text-lg hover:bg-yellow-300 transition-colors">
                DETAILS
              </button>
            </div>
          ))}
        </div>

        {/* SYSTEM STATUS: BIG & CLEAR */}
        <div className="grid grid-cols-4 gap-6 mt-8">
          <div className="bg-green-900 border-4 border-green-400 rounded-xl p-6 text-center">
            <p className="text-4xl font-black text-green-400">✅</p>
            <p className="text-xl font-black text-green-400 mt-3">SYSTEM OK</p>
            <p className="text-gray-300 text-lg mt-2">All Systems Operational</p>
          </div>

          <div className="bg-blue-900 border-4 border-blue-400 rounded-xl p-6 text-center">
            <p className="text-4xl font-black text-blue-400">📡</p>
            <p className="text-xl font-black text-blue-400 mt-3">ONLINE</p>
            <p className="text-gray-300 text-lg mt-2">Connected to Server</p>
          </div>

          <div className="bg-yellow-900 border-4 border-yellow-400 rounded-xl p-6 text-center">
            <p className="text-4xl font-black text-yellow-400">⚠️</p>
            <p className="text-xl font-black text-yellow-400 mt-3">2 ISSUES</p>
            <p className="text-gray-300 text-lg mt-2">Attention Required</p>
          </div>

          <div className="bg-purple-900 border-4 border-purple-400 rounded-xl p-6 text-center">
            <p className="text-4xl font-black text-purple-400">📦</p>
            <p className="text-xl font-black text-purple-400 mt-3">245 ITEMS</p>
            <p className="text-gray-300 text-lg mt-2">In System</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// MOCKUP 5: COMPONENT-BASED ARCHITECTURE
// TypeScript interfaces and reusable components for modern React
// ============================================================================

// Core Types
interface Item {
  id: string;
  delivery_number: string;
  article_number: string;
  batch_number: string;
  quantity: number;
  status: ItemStatus;
  created_at: Date;
  last_updated: Date;
}

type ItemStatus = 'pending' | 'data_checked' | 'docs_checked' | 'measured' | 'completed';

interface ItemTableProps {
  items: Item[];
  onEdit: (item: Item) => void;
  onDelete: (itemId: string) => void;
  onSelectForAction: (item: Item) => void;
  isLoading?: boolean;
}

interface FilterState {
  searchQuery: string;
  status: ItemStatus | 'all';
  dateRange: 'today' | 'week' | 'month';
  sortBy: 'date' | 'status' | 'article';
}

// Reusable Components
const ItemTableComponent: React.FC<ItemTableProps> = ({
  items,
  onEdit,
  onDelete,
  onSelectForAction,
  isLoading,
}) => {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-gray-100 border-b-2 border-gray-300">
            <th className="px-4 py-3 text-left text-sm font-bold text-gray-900">Delivery</th>
            <th className="px-4 py-3 text-left text-sm font-bold text-gray-900">Article</th>
            <th className="px-4 py-3 text-left text-sm font-bold text-gray-900">Batch</th>
            <th className="px-4 py-3 text-left text-sm font-bold text-gray-900">Status</th>
            <th className="px-4 py-3 text-left text-sm font-bold text-gray-900">Qty</th>
            <th className="px-4 py-3 text-right text-sm font-bold text-gray-900">Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} className="border-b border-gray-200 hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3 text-sm font-mono text-blue-600">{item.delivery_number}</td>
              <td className="px-4 py-3 text-sm font-mono text-gray-900">{item.article_number}</td>
              <td className="px-4 py-3 text-sm text-gray-600">{item.batch_number}</td>
              <td className="px-4 py-3 text-sm">
                <StatusBadge status={item.status} />
              </td>
              <td className="px-4 py-3 text-sm font-bold text-gray-900">{item.quantity}</td>
              <td className="px-4 py-3 text-sm flex gap-2 justify-end">
                <button
                  onClick={() => onEdit(item)}
                  className="text-blue-600 hover:text-blue-900 font-bold"
                >
                  Edit
                </button>
                <button
                  onClick={() => onDelete(item.id)}
                  className="text-red-600 hover:text-red-900 font-bold"
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const StatusBadge: React.FC<{ status: ItemStatus }> = ({ status }) => {
  const statusConfig = {
    pending: { bg: 'bg-gray-100', text: 'text-gray-800', label: 'Pending' },
    data_checked: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Data Checked' },
    docs_checked: { bg: 'bg-green-100', text: 'text-green-800', label: 'Docs Checked' },
    measured: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Measured' },
    completed: { bg: 'bg-purple-100', text: 'text-purple-800', label: 'Completed' },
  };

  const config = statusConfig[status];
  return (
    <span className={`inline-block ${config.bg} ${config.text} px-3 py-1 rounded-full text-xs font-bold`}>
      {config.label}
    </span>
  );
};

const FilterBar: React.FC<{
  filters: FilterState;
  onFilterChange: (filters: FilterState) => void;
}> = ({ filters, onFilterChange }) => {
  return (
    <div className="bg-white border border-gray-300 rounded-lg p-4 space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Search Input */}
        <div>
          <label className="block text-sm font-bold text-gray-700 mb-2">Search</label>
          <input
            type="text"
            placeholder="Delivery, Article..."
            value={filters.searchQuery}
            onChange={(e) => onFilterChange({ ...filters, searchQuery: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
          />
        </div>

        {/* Status Filter */}
        <div>
          <label className="block text-sm font-bold text-gray-700 mb-2">Status</label>
          <select
            value={filters.status}
            onChange={(e) => onFilterChange({ ...filters, status: e.target.value as any })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
          >
            <option value="all">All</option>
            <option value="pending">Pending</option>
            <option value="data_checked">Data Checked</option>
            <option value="docs_checked">Docs Checked</option>
            <option value="measured">Measured</option>
          </select>
        </div>

        {/* Date Range */}
        <div>
          <label className="block text-sm font-bold text-gray-700 mb-2">Date Range</label>
          <select
            value={filters.dateRange}
            onChange={(e) => onFilterChange({ ...filters, dateRange: e.target.value as any })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
          >
            <option value="today">Today</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
          </select>
        </div>

        {/* Sort */}
        <div>
          <label className="block text-sm font-bold text-gray-700 mb-2">Sort By</label>
          <select
            value={filters.sortBy}
            onChange={(e) => onFilterChange({ ...filters, sortBy: e.target.value as any })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
          >
            <option value="date">Newest First</option>
            <option value="status">By Status</option>
            <option value="article">By Article</option>
          </select>
        </div>
      </div>
    </div>
  );
};

export const ComponentBasedUI: React.FC = () => {
  const [items, setItems] = useState<Item[]>([
    {
      id: '1',
      delivery_number: 'LS-2024-0001',
      article_number: 'ART-12341',
      batch_number: 'BATCH-2024-001',
      quantity: 50,
      status: 'data_checked',
      created_at: new Date(),
      last_updated: new Date(),
    },
  ]);

  const [filters, setFilters] = useState<FilterState>({
    searchQuery: '',
    status: 'all',
    dateRange: 'today',
    sortBy: 'date',
  });

  const handleEdit = (item: Item) => {
    console.log('Edit:', item);
  };

  const handleDelete = (itemId: string) => {
    setItems(items.filter((i) => i.id !== itemId));
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Component-Based Warehouse UI</h1>
          <p className="text-gray-600 mt-2">Modern, Type-Safe TypeScript/React Architecture</p>
        </div>

        <div className="space-y-6">
          <FilterBar filters={filters} onFilterChange={setFilters} />
          <ItemTableComponent items={items} onEdit={handleEdit} onDelete={handleDelete} onSelectForAction={handleEdit} />
        </div>
      </div>
    </div>
  );
};
