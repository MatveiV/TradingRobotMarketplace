import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { strategiesApi } from '../services/api';
import { Strategy } from '../types';

const StrategiesPage: React.FC = () => {
  const navigate = useNavigate();
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadStrategies(); }, []);

  const loadStrategies = async () => {
    try {
      const data = await strategiesApi.list();
      setStrategies(data);
    } catch (err) {
      console.error('Failed to load strategies:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusStyle = (status: string) => {
    const map: Record<string, string> = {
      running: 'bg-emerald-100 text-emerald-800 border-emerald-200',
      published: 'bg-blue-100 text-blue-800 border-blue-200',
      pending_moderation: 'bg-amber-100 text-amber-800 border-amber-200',
      draft: 'bg-gray-100 text-gray-800 border-gray-200',
      approved: 'bg-emerald-100 text-emerald-800 border-emerald-200',
      rejected: 'bg-red-100 text-red-800 border-red-200',
      stopped: 'bg-gray-100 text-gray-800 border-gray-200',
      error: 'bg-red-100 text-red-800 border-red-200',
    };
    return map[status] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const statusLabels: Record<string, string> = {
    draft: 'Черновик', pending_moderation: 'На модерации', approved: 'Одобрена',
    published: 'Опубликована', rejected: 'Отклонена', running: 'Активна',
    stopped: 'Остановлена', error: 'Ошибка',
  };

  const totalInvestors = strategies.reduce((s, x) => s + x.investors_count, 0);
  const totalAum = strategies.reduce((s, x) => s + x.aum, 0);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="gradient-header text-white relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-10 relative">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold">Панель управляющего</h1>
              <p className="text-blue-200 mt-1">Управляйте своими стратегиями и отслеживайте инвесторов</p>
            </div>
            <Link to="/create"
              className="bg-white text-blue-700 px-5 py-2.5 rounded-xl font-bold text-sm hover:bg-blue-50 transition shadow-lg">
              + Новая стратегия
            </Link>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { value: strategies.length, label: 'Стратегий', icon: '📊' },
              { value: totalInvestors, label: 'Инвесторов', icon: '👥' },
              { value: `$${totalAum.toLocaleString()}`, label: 'Под управлением', icon: '💰' },
              { value: strategies.filter(s => s.status === 'published' || s.status === 'running').length, label: 'Активных', icon: '✅' },
            ].map((s) => (
              <div key={s.label} className="bg-white/10 backdrop-blur-sm rounded-xl p-3.5 text-center border border-white/10">
                <div className="text-xl font-bold">{s.value}</div>
                <div className="text-xs text-blue-200 mt-0.5">{s.icon} {s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-4 mb-8">
        <button onClick={() => navigate('/')}
          className="bg-white shadow-sm border border-gray-200 px-4 py-2 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-50 transition">
          ← Marketplace
        </button>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
        {loading ? (
          <div className="text-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-2 border-blue-600 border-t-transparent mx-auto"></div>
            <p className="text-gray-500 mt-4 font-medium">Загрузка...</p>
          </div>
        ) : strategies.length === 0 ? (
          <div className="bg-white rounded-2xl p-16 text-center shadow-sm border border-gray-100">
            <div className="w-20 h-20 bg-gradient-to-br from-blue-100 to-blue-200 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <span className="text-4xl">🤖</span>
            </div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">У вас нет стратегий</h2>
            <p className="text-gray-500 mb-8 max-w-md mx-auto">Создайте первую стратегию и начните зарабатывать на комиссии от инвесторов.</p>
            <Link to="/create"
              className="btn-primary text-white px-8 py-3.5 rounded-xl font-bold text-base shadow-lg shadow-blue-500/25 inline-block">
              Создать стратегию
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {strategies.map((s) => (
              <div key={s.id} onClick={() => navigate(`/strategies/${s.id}`)}
                className="bg-white rounded-2xl p-5 sm:p-6 shadow-sm border border-gray-100 card-hover cursor-pointer">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-700 rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-md flex-shrink-0">
                      {s.name.charAt(0)}
                    </div>
                    <div>
                      <h3 className="font-bold text-gray-900">{s.name}</h3>
                      <p className="text-sm text-gray-500 mt-0.5">
                        {s.platform_type.toUpperCase()} · {s.subscription_type} · ${s.price}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 sm:text-right">
                    <div className="text-xs sm:text-sm text-gray-500">
                      <div className="font-semibold text-gray-800">{s.investors_count} инв.</div>
                      <div>${s.aum.toLocaleString()}</div>
                    </div>
                    <span className={`px-3 py-1.5 rounded-lg text-xs font-semibold border ${getStatusStyle(s.status)}`}>
                      {statusLabels[s.status] || s.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default StrategiesPage;
