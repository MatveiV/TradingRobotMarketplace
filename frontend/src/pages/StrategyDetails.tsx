import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { strategiesApi } from '../services/api';
import { Strategy, PerformanceData } from '../types';

const StrategyDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [performance, setPerformance] = useState<PerformanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [investment, setInvestment] = useState(1000);
  const [showInvestForm, setShowInvestForm] = useState(false);

  useEffect(() => {
    if (id) loadStrategy(parseInt(id));
  }, [id]);

  const loadStrategy = async (strategyId: number) => {
    try {
      setLoading(true);
      const [s, p] = await Promise.all([
        strategiesApi.get(strategyId),
        strategiesApi.getPerformance(strategyId).catch(() => null)
      ]);
      setStrategy(s);
      setPerformance(p);
    } catch (err: any) {
      setError(err.message || 'Ошибка загрузки');
    } finally {
      setLoading(false);
    }
  };

  const actions: Record<string, { label: string; action: () => void; style: string }[]> = {};

  const handleConnect = async () => {
    if (!strategy) return;
    try {
      await strategiesApi.connect(strategy.id);
      await loadStrategy(strategy.id);
      setSuccess('Подключение выполнено');
    } catch (err: any) { setError(err.message); }
  };

  const handleStart = async () => {
    if (!strategy) return;
    try {
      await strategiesApi.start(strategy.id);
      await loadStrategy(strategy.id);
      setSuccess('Робот запущен');
    } catch (err: any) { setError(err.message); }
  };

  const handleStop = async () => {
    if (!strategy) return;
    try {
      await strategiesApi.stop(strategy.id);
      await loadStrategy(strategy.id);
      setSuccess('Робот остановлен');
    } catch (err: any) { setError(err.message); }
  };

  const handleSubmitModeration = async () => {
    if (!strategy) return;
    try {
      await strategiesApi.submitForModeration(strategy.id);
      await loadStrategy(strategy.id);
      setSuccess('Отправлено на модерацию');
    } catch (err: any) { setError(err.message); }
  };

  const handleApprove = async () => {
    if (!strategy) return;
    try {
      await strategiesApi.approve(strategy.id);
      await loadStrategy(strategy.id);
      setSuccess('Стратегия опубликована');
    } catch (err: any) { setError(err.message); }
  };

  const handleInvestorConnect = async () => {
    if (!strategy) return;
    try {
      const result = await strategiesApi.investorConnect(strategy.id, investment);
      setSuccess(`Подключено! ID подключения: ${result.connection_id}`);
      setShowInvestForm(false);
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message;
      setError(typeof detail === 'string' ? detail : detail?.message || 'Ошибка подключения');
    }
  };

  if (loading) return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-2 border-blue-600 border-t-transparent mx-auto"></div>
        <p className="text-gray-500 mt-4 font-medium">Загрузка...</p>
      </div>
    </div>
  );

  if (!strategy) return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 bg-red-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <span className="text-3xl">🔍</span>
        </div>
        <h2 className="text-xl font-bold text-gray-800 mb-2">Стратегия не найдена</h2>
        <button onClick={() => navigate('/')} className="text-blue-600 hover:underline font-medium">← Вернуться</button>
      </div>
    </div>
  );

  const perfData = performance || strategy.performance_data || { total_profit: 0, total_trades: 0, winning_trades: 0, losing_trades: 0, win_rate: 0, trades: [] };
  const profitColor = perfData.total_profit >= 0 ? 'text-emerald-600' : 'text-red-600';
  const isPublished = strategy.status === 'published';

  const getStatusBadge = () => {
    const map: Record<string, string> = {
      running: 'bg-emerald-100 text-emerald-800', published: 'bg-blue-100 text-blue-800',
      pending_moderation: 'bg-amber-100 text-amber-800', draft: 'bg-gray-100 text-gray-800',
      approved: 'bg-emerald-100 text-emerald-800', rejected: 'bg-red-100 text-red-800',
      stopped: 'bg-gray-100 text-gray-800', error: 'bg-red-100 text-red-800',
    };
    return map[strategy.status] || 'bg-gray-100 text-gray-800';
  };

  const statusLabels: Record<string, string> = {
    draft: 'Черновик', pending_moderation: 'На модерации', approved: 'Одобрена',
    published: 'Опубликована', rejected: 'Отклонена', running: 'Активна',
    stopped: 'Остановлена', error: 'Ошибка',
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Top bar */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between">
          <button onClick={() => navigate('/')} className="text-gray-500 hover:text-gray-800 flex items-center gap-1.5 text-sm font-medium transition">
            <span className="text-lg">←</span> {isPublished ? 'К списку стратегий' : 'Мои стратегии'}
          </button>
          <div className="flex items-center gap-3">
            <span className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${getStatusBadge()}`}>
              {statusLabels[strategy.status] || strategy.status}
            </span>
            {!isPublished && (
              <button onClick={() => navigate('/strategies')}
                className="px-4 py-1.5 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition">
                🔧 Dashboard
              </button>
            )}
          </div>
        </div>
      </div>

      {error && (
        <div className="max-w-7xl mx-auto px-4 mt-4">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl flex justify-between items-center">
            <span className="font-medium text-sm">⚠ {error}</span>
            <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700">✕</button>
          </div>
        </div>
      )}
      {success && (
        <div className="max-w-7xl mx-auto px-4 mt-4">
          <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 px-4 py-3 rounded-xl flex justify-between items-center">
            <span className="font-medium text-sm">✓ {success}</span>
            <button onClick={() => setSuccess(null)} className="text-emerald-500 hover:text-emerald-700">✕</button>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Hero card */}
        <div className="gradient-header rounded-2xl p-6 sm:p-8 text-white relative overflow-hidden mb-6">
          <div className="absolute inset-0 opacity-10" style={{
            backgroundImage: 'radial-gradient(circle at 30% 50%, rgba(255,255,255,0.15) 0%, transparent 50%)'
          }}></div>
          <div className="relative flex flex-col sm:flex-row items-start gap-6">
            <div className="w-16 h-16 sm:w-20 sm:h-20 bg-gradient-to-br from-white/20 to-white/5 rounded-2xl flex items-center justify-center text-white font-bold text-3xl border border-white/20 backdrop-blur-sm flex-shrink-0">
              {strategy.name.charAt(0)}
            </div>
            <div className="flex-1">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h1 className="text-2xl sm:text-3xl font-extrabold">{strategy.name}</h1>
                  <p className="text-blue-200 mt-1 font-medium">{strategy.money_manager_name || 'Anonymous'} · {strategy.platform_type.toUpperCase()}</p>
                </div>
                <div className="text-right">
                  <div className={`text-3xl sm:text-4xl font-extrabold ${profitColor}`}>
                    {perfData.total_profit >= 0 ? '+' : ''}{perfData.total_profit.toFixed(1)}%
                  </div>
                  <div className="text-blue-200 text-sm">общая доходность</div>
                </div>
              </div>
              <p className="mt-3 text-blue-100 text-sm leading-relaxed max-w-2xl">{strategy.description}</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Stats grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                { value: perfData.total_trades, label: 'Всего сделок', color: 'text-blue-600', bg: 'bg-blue-50 border-blue-100', icon: '📊' },
                { value: `${perfData.win_rate.toFixed(1)}%`, label: 'Прибыльных', color: 'text-emerald-600', bg: 'bg-emerald-50 border-emerald-100', icon: '✅' },
                { value: perfData.winning_trades, label: 'Выигрыш', color: 'text-emerald-600', bg: 'bg-emerald-50 border-emerald-100', icon: '📈' },
                { value: perfData.losing_trades, label: 'Проигрыш', color: 'text-red-600', bg: 'bg-red-50 border-red-100', icon: '📉' },
              ].map((stat) => (
                <div key={stat.label} className={`${stat.bg} border rounded-xl p-4 text-center card-hover`}>
                  <div className="text-xl mb-1">{stat.icon}</div>
                  <div className={`text-xl sm:text-2xl font-extrabold ${stat.color}`}>{stat.value}</div>
                  <div className="text-xs text-gray-500 font-medium mt-0.5">{stat.label}</div>
                </div>
              ))}
            </div>

            {/* Win rate bar */}
            {perfData.total_trades > 0 && (
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <span className="text-lg">📈</span> Статистика торговли
                </h3>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1.5">
                      <span className="text-gray-600 font-medium">Win Rate</span>
                      <span className="font-bold text-emerald-600">{perfData.win_rate.toFixed(1)}%</span>
                    </div>
                    <div className="progress-bar">
                      <div className="progress-fill bg-gradient-to-r from-emerald-400 to-emerald-600" style={{width: `${perfData.win_rate}%`}}></div>
                    </div>
                  </div>
                  <div className="flex gap-4 text-sm">
                    <div className="flex items-center gap-2 bg-emerald-50 rounded-lg px-3 py-2">
                      <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
                      <span className="text-emerald-700 font-medium">Выигрыш: {perfData.winning_trades}</span>
                    </div>
                    <div className="flex items-center gap-2 bg-red-50 rounded-lg px-3 py-2">
                      <div className="w-3 h-3 rounded-full bg-red-500"></div>
                      <span className="text-red-700 font-medium">Проигрыш: {perfData.losing_trades}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Details card */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
              <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                <span className="text-lg">ℹ️</span> Детали стратегии
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
                {[
                  { label: 'Платформа', value: strategy.platform_type.toUpperCase(), icon: '🖥' },
                  { label: 'Риск', value: strategy.risk_level === 'low' ? 'Низкий' : strategy.risk_level === 'medium' ? 'Средний' : 'Высокий', icon: '⚠️' },
                  { label: 'Комиссия', value: `${strategy.commission_percent}%`, icon: '💼' },
                  { label: 'Инвесторы', value: strategy.investors_count, icon: '👥' },
                  { label: 'Подписка', value: `$${strategy.price}/${strategy.subscription_type}`, icon: '💳' },
                  { label: 'AUM', value: `$${strategy.aum.toLocaleString()}`, icon: '💰' },
                ].map((item) => (
                  <div key={item.label} className="bg-gray-50 rounded-xl p-3.5 text-center border border-gray-100">
                    <div className="text-lg mb-1">{item.icon}</div>
                    <div className="text-sm font-bold text-gray-900">{item.value}</div>
                    <div className="text-xs text-gray-500 mt-0.5">{item.label}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Trading History */}
            {perfData.trades && perfData.trades.length > 0 && (
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <span className="text-lg">📋</span> История сделок
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-100">
                        <th className="text-left py-3 px-2 text-gray-500 font-semibold">Символ</th>
                        <th className="text-left py-3 px-2 text-gray-500 font-semibold">Тип</th>
                        <th className="text-left py-3 px-2 text-gray-500 font-semibold">Объём</th>
                        <th className="text-right py-3 px-2 text-gray-500 font-semibold">Прибыль</th>
                        <th className="text-right py-3 px-2 text-gray-500 font-semibold">Дата</th>
                      </tr>
                    </thead>
                    <tbody>
                      {perfData.trades.slice(-15).map((trade) => (
                        <tr key={trade.id} className="border-b border-gray-50 hover:bg-gray-50 transition">
                          <td className="py-3 px-2 font-semibold text-gray-900">{trade.symbol}</td>
                          <td className="py-3 px-2">
                            <span className={`px-2.5 py-1 rounded-lg text-xs font-bold ${
                              trade.type === 'buy' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                            }`}>
                              {trade.type === 'buy' ? 'BUY' : 'SELL'}
                            </span>
                          </td>
                          <td className="py-3 px-2 text-gray-600">{trade.volume || '-'}</td>
                          <td className={`py-3 px-2 text-right font-bold ${(trade.profit || 0) >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                            ${(trade.profit || 0).toFixed(2)}
                          </td>
                          <td className="py-3 px-2 text-right text-gray-400 text-xs">
                            {new Date(trade.timestamp).toLocaleDateString('ru-RU')}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* MM Profile */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
              <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                <span className="text-lg">👤</span> Управляющий
              </h3>
              <div className="flex items-center gap-4 mb-4">
                <div className="w-14 h-14 bg-gradient-to-br from-blue-400 to-blue-600 rounded-xl flex items-center justify-center text-white font-bold text-xl shadow-md">
                  {(strategy.money_manager_name || 'A').charAt(0)}
                </div>
                <div>
                  <p className="font-bold text-gray-900">{strategy.money_manager_name || 'Anonymous'}</p>
                  <p className="text-sm text-gray-500 flex items-center gap-1 mt-0.5">
                    <span className={`px-2 py-0.5 rounded text-xs font-bold text-white ${
                      strategy.platform_type === 'mt4' ? 'platform-badge-mt4' : 'platform-badge-mt5'
                    }`}>{strategy.platform_type.toUpperCase()}</span>
                  </p>
                </div>
              </div>
              <div className="text-xs text-gray-400 space-y-1 pt-3 border-t border-gray-100">
                <p>Стратегия создана: {new Date(strategy.created_at).toLocaleDateString('ru-RU')}</p>
                <p>Комиссия: {strategy.commission_percent}% от прибыли</p>
                <p>Риск: {strategy.risk_level === 'low' ? 'Низкий' : strategy.risk_level === 'medium' ? 'Средний' : 'Высокий'}</p>
              </div>
            </div>

            {/* MM Actions */}
            {!isPublished && (
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <span className="text-lg">⚙️</span> Управление
                </h3>
                <div className="space-y-3">
                  {(strategy.status === 'draft' || strategy.status === 'stopped') && (
                    <>
                      {strategy.status === 'draft' && (
                        <button onClick={handleConnect}
                          className="w-full py-3 btn-primary text-white rounded-xl font-semibold text-sm shadow-lg shadow-blue-500/25">
                          🔌 Подключить
                        </button>
                      )}
                      <button onClick={handleStart}
                        className="w-full py-3 btn-success text-white rounded-xl font-semibold text-sm shadow-lg shadow-emerald-500/25">
                        ▶️ Запустить робота
                      </button>
                      {strategy.status === 'draft' && (
                        <button onClick={handleSubmitModeration}
                          className="w-full py-3 bg-gradient-to-r from-amber-500 to-amber-600 text-white rounded-xl font-semibold text-sm hover:shadow-lg hover:shadow-amber-500/25 transition">
                          📋 Отправить на модерацию
                        </button>
                      )}
                    </>
                  )}
                  {strategy.status === 'running' && (
                    <button onClick={handleStop}
                      className="w-full py-3 btn-danger text-white rounded-xl font-semibold text-sm shadow-lg shadow-red-500/25">
                      ⏹ Остановить робота
                    </button>
                  )}
                  {strategy.status === 'pending_moderation' && (
                    <button onClick={handleApprove}
                      className="w-full py-3 btn-success text-white rounded-xl font-semibold text-sm shadow-lg shadow-emerald-500/25">
                      ✅ Опубликовать (Admin)
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Investor Connect */}
            {isPublished && (
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <span className="text-lg">💎</span> Инвестировать
                </h3>
                {!showInvestForm ? (
                  <div className="space-y-4">
                    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-100">
                      <div className="text-sm text-gray-600 space-y-2">
                        <div className="flex items-center gap-2 text-emerald-600">
                          <span>✓</span> Комиссия: {strategy.commission_percent}% от прибыли
                        </div>
                        <div className="flex items-center gap-2 text-blue-600">
                          <span>✓</span> Копируются только новые сделки
                        </div>
                        <div className="flex items-center gap-2 text-gray-500">
                          <span>✓</span> Отписка в любой момент
                        </div>
                      </div>
                    </div>
                    <button onClick={() => setShowInvestForm(true)}
                      className="w-full py-3 btn-primary text-white rounded-xl font-semibold text-sm shadow-lg shadow-blue-500/25">
                      💳 Подключиться к стратегии
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm text-gray-600 font-medium block mb-1.5">Сумма инвестиций ($)</label>
                      <input type="number" value={investment} min={0}
                        onChange={(e) => setInvestment(Number(e.target.value))}
                        className="input-field text-lg font-bold" />
                    </div>
                    <div className="bg-gradient-to-br from-amber-50 to-yellow-50 rounded-xl p-3 border border-amber-100">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Комиссия MM:</span>
                        <span className="font-bold text-amber-600">{strategy.commission_percent}%</span>
                      </div>
                      <div className="flex justify-between text-sm mt-1">
                        <span className="text-gray-600">Ежедневное списание:</span>
                        <span className="font-bold text-gray-900">${(investment * strategy.commission_percent / 100).toFixed(2)}</span>
                      </div>
                    </div>
                    <div className="flex gap-3">
                      <button onClick={() => setShowInvestForm(false)}
                        className="flex-1 py-3 bg-gray-100 text-gray-700 rounded-xl font-semibold text-sm hover:bg-gray-200 transition">
                        Отмена
                      </button>
                      <button onClick={handleInvestorConnect}
                        className="flex-1 py-3 btn-primary text-white rounded-xl font-semibold text-sm shadow-lg shadow-blue-500/25">
                        Подключить
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StrategyDetails;
