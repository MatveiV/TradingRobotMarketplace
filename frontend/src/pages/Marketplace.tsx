import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { strategiesApi } from '../services/api';
import { MarketplaceStrategy } from '../types';

const Marketplace: React.FC = () => {
  const navigate = useNavigate();
  const [strategies, setStrategies] = useState<MarketplaceStrategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterPlatform, setFilterPlatform] = useState('');
  const [filterRisk, setFilterRisk] = useState('');
  const [sortBy, setSortBy] = useState('');
  const [showMmVoice, setShowMmVoice] = useState(false);

  useEffect(() => {
    loadMarketplace();
  }, [filterPlatform, filterRisk, sortBy]);

  const loadMarketplace = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (filterPlatform) params.platform = filterPlatform;
      if (filterRisk) params.risk = filterRisk;
      if (sortBy) params.sort_by = sortBy;
      const data = await strategiesApi.getMarketplace(params);
      setStrategies(data);
    } catch (err) {
      console.error('Failed to load marketplace:', err);
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'text-emerald-600 bg-emerald-50 border-emerald-200';
      case 'medium': return 'text-amber-600 bg-amber-50 border-amber-200';
      case 'high': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Hero Section */}
      <div className="gradient-header text-white relative overflow-hidden">
        <div className="absolute inset-0 opacity-10" style={{
          backgroundImage: 'radial-gradient(circle at 25% 50%, rgba(255,255,255,0.1) 0%, transparent 50%), radial-gradient(circle at 75% 50%, rgba(255,255,255,0.05) 0%, transparent 50%)'
        }}></div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-10 relative">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight">
                Copy Trading
              </h1>
              <p className="mt-3 text-blue-200 text-base sm:text-lg max-w-2xl">
                Автоматически копируйте сделки лучших трейдеров. Выберите управляющего и начните зарабатывать вместе с профессионалами.
              </p>
              <div className="flex flex-wrap gap-4 mt-6">
                <div className="flex items-center gap-2 bg-white/10 backdrop-blur-sm rounded-xl px-4 py-2.5">
                  <span className="text-2xl">📊</span>
                  <div>
                    <div className="text-lg font-bold">{strategies.length}</div>
                    <div className="text-xs text-blue-200">Стратегий</div>
                  </div>
                </div>
                <div className="flex items-center gap-2 bg-white/10 backdrop-blur-sm rounded-xl px-4 py-2.5">
                  <span className="text-2xl">💰</span>
                  <div>
                    <div className="text-lg font-bold">
                      ${strategies.reduce((s, x) => s + x.aum, 0).toLocaleString()}
                    </div>
                    <div className="text-xs text-blue-200">Под управлением</div>
                  </div>
                </div>
                <div className="flex items-center gap-2 bg-white/10 backdrop-blur-sm rounded-xl px-4 py-2.5">
                  <span className="text-2xl">👥</span>
                  <div>
                    <div className="text-lg font-bold">
                      {strategies.reduce((s, x) => s + x.investors_count, 0)}
                    </div>
                    <div className="text-xs text-blue-200">Инвесторов</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="hidden lg:flex flex-col items-end gap-3">
              <button onClick={() => navigate('/strategies')}
                className="bg-white/10 backdrop-blur-sm border border-white/20 text-white px-6 py-3 rounded-xl font-semibold hover:bg-white/20 transition text-sm">
                🔧 Я управляющий
              </button>
            </div>
          </div>

          {/* How it works steps */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-8 bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
            {[
              { step: '1', title: 'Выберите стратегию', desc: 'Просмотрите доходность, риск и комиссию управляющих' },
              { step: '2', title: 'Подключите счёт', desc: 'Пополните баланс и нажмите "Connect to Strategy"' },
              { step: '3', title: 'Копируйте сделки', desc: 'Сделки управляющего автоматически повторяются на вашем счёте' },
            ].map((item) => (
              <div key={item.step} className="flex items-start gap-3">
                <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center text-sm font-bold flex-shrink-0">
                  {item.step}
                </div>
                <div>
                  <div className="font-semibold text-sm">{item.title}</div>
                  <div className="text-xs text-blue-200 mt-0.5">{item.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 mb-8 relative z-10">
        <div className="glass rounded-2xl shadow-lg border border-gray-100 p-4 sm:p-5 flex flex-wrap items-center gap-3">
          <span className="text-sm font-semibold text-gray-600 mr-1">🔍 Фильтры:</span>
          <select value={filterPlatform} onChange={(e) => setFilterPlatform(e.target.value)}
            className="px-4 py-2.5 border border-gray-200 rounded-xl text-sm outline-none bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition">
            <option value="">Все платформы</option>
            <option value="mt4">MetaTrader 4</option>
            <option value="mt5">MetaTrader 5</option>
          </select>
          <select value={filterRisk} onChange={(e) => setFilterRisk(e.target.value)}
            className="px-4 py-2.5 border border-gray-200 rounded-xl text-sm outline-none bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition">
            <option value="">Все уровни риска</option>
            <option value="low">Низкий риск</option>
            <option value="medium">Средний риск</option>
            <option value="high">Высокий риск</option>
          </select>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}
            className="px-4 py-2.5 border border-gray-200 rounded-xl text-sm outline-none bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition">
            <option value="">По дате</option>
            <option value="profit">По доходности</option>
            <option value="investors">По популярности</option>
          </select>
          <div className="flex-1"></div>
          <button onClick={() => navigate('/create')}
            className="btn-primary text-white px-5 py-2.5 rounded-xl font-semibold text-sm shadow-lg shadow-blue-500/25">
            + Создать стратегию
          </button>
        </div>
      </div>

      {/* Strategy Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
        {loading ? (
          <div className="text-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-2 border-blue-600 border-t-transparent mx-auto"></div>
            <p className="text-gray-500 mt-4 font-medium">Загрузка стратегий...</p>
          </div>
        ) : strategies.length === 0 ? (
          <div className="text-center py-20">
            <div className="w-20 h-20 bg-gradient-to-br from-blue-100 to-blue-200 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <span className="text-4xl">📊</span>
            </div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Стратегий пока нет</h2>
            <p className="text-gray-500 mb-8 max-w-md mx-auto">
              Станьте первым управляющим и начните зарабатывать на комиссии от инвесторов.
            </p>
            <button onClick={() => navigate('/create')}
              className="btn-primary text-white px-8 py-3.5 rounded-xl font-semibold text-base shadow-lg shadow-blue-500/25">
              Создать стратегию
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {strategies.map((s) => (
              <div key={s.id} onClick={() => navigate(`/strategies/${s.id}`)}
                className="bg-white rounded-2xl shadow-sm border border-gray-100 card-hover cursor-pointer overflow-hidden">
                
                {/* Card header */}
                <div className="p-5 pb-3">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-700 rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-md">
                        {s.name.charAt(0)}
                      </div>
                      <div>
                        <h3 className="font-bold text-gray-900 leading-tight">{s.name}</h3>
                        <p className="text-xs text-gray-500 mt-0.5">by {s.mm_name}</p>
                      </div>
                    </div>
                    <span className={`px-2.5 py-1 rounded-lg text-xs font-semibold border ${getRiskColor(s.risk_level)}`}>
                      {s.risk_level === 'low' ? 'Низкий' : s.risk_level === 'medium' ? 'Средний' : 'Высокий'}
                    </span>
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-gradient-to-br from-emerald-50 to-green-50 rounded-xl p-3.5 text-center border border-emerald-100">
                      <div className="text-xl font-extrabold text-emerald-600">+{s.profit_percent}%</div>
                      <div className="text-xs text-emerald-600 font-medium mt-0.5">Доходность</div>
                    </div>
                    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-3.5 text-center border border-blue-100">
                      <div className="text-xl font-extrabold text-blue-600">{s.commission_percent}%</div>
                      <div className="text-xs text-blue-600 font-medium mt-0.5">Комиссия</div>
                    </div>
                  </div>
                </div>

                {/* Card footer */}
                <div className="px-5 py-3.5 bg-gray-50/80 border-t border-gray-100">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-1.5 text-gray-600">
                      <span className="text-base">👥</span>
                      <span className="font-semibold">{s.investors_count}</span>
                      <span className="text-gray-400">инв.</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-gray-600">
                      <span className="text-base">💰</span>
                      <span className="font-semibold">${s.aum.toLocaleString()}</span>
                    </div>
                    <span className={`px-2.5 py-1 rounded-lg text-xs font-bold text-white ${
                      s.platform === 'mt4' ? 'platform-badge-mt4' : 'platform-badge-mt5'
                    }`}>
                      {s.platform.toUpperCase()}
                    </span>
                  </div>
                  <button onClick={(e) => { e.stopPropagation(); navigate(`/strategies/${s.id}`); }}
                    className="w-full mt-3 py-2.5 bg-blue-600 text-white rounded-xl font-semibold text-sm hover:bg-blue-700 transition shadow-md shadow-blue-500/20">
                    Подробнее
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Marketplace;
