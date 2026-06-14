import React from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import CreateStrategy from './pages/CreateStrategy';
import StrategiesPage from './pages/StrategiesPage';
import StrategyDetails from './pages/StrategyDetails';
import Marketplace from './pages/Marketplace';

function NavBar() {
  const location = useLocation();
  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14 sm:h-16">
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-2 font-extrabold text-lg text-gray-900">
              <span className="w-8 h-8 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg flex items-center justify-center text-white text-sm">CT</span>
              <span className="hidden sm:inline">CopyTrade</span>
            </Link>
            <div className="flex items-center gap-1 sm:gap-2">
              <Link to="/"
                className={`px-3 sm:px-4 py-2 rounded-xl text-sm font-semibold transition ${
                  isActive('/') && !isActive('/strategies') && !location.pathname.startsWith('/create')
                    ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}>
                Marketplace
              </Link>
              <Link to="/strategies"
                className={`px-3 sm:px-4 py-2 rounded-xl text-sm font-semibold transition ${
                  isActive('/strategies') ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}>
                Управляющим
              </Link>
            </div>
          </div>
          <Link to="/create"
            className="btn-primary text-white px-4 sm:px-5 py-2 rounded-xl font-semibold text-sm shadow-lg shadow-blue-500/25">
            + Создать
          </Link>
        </div>
      </div>
    </nav>
  );
}

function App() {
  return (
    <BrowserRouter>
      <NavBar />
      <Routes>
        <Route path="/" element={<Marketplace />} />
        <Route path="/strategies" element={<StrategiesPage />} />
        <Route path="/strategies/:id" element={<StrategyDetails />} />
        <Route path="/create" element={<CreateStrategy />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
