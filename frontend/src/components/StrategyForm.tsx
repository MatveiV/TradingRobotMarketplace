import React, { useState } from 'react';
import { CreateStrategyFormData } from '../types';

interface StrategyFormProps {
  onSubmit: (formData: FormData) => void;
  isLoading: boolean;
}

const StrategyForm: React.FC<StrategyFormProps> = ({ onSubmit, isLoading }) => {
  const [platformType, setPlatformType] = useState<'mt4' | 'mt5'>('mt4');
  const [formData, setFormData] = useState<Partial<CreateStrategyFormData>>({
    subscription_type: 'monthly',
    price: 0,
    commission_percent: 0,
    risk_level: 'medium',
    execution_type: 'sequential',
  });

  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [robotFile, setRobotFile] = useState<File | null>(null);
  const [settingsFile, setSettingsFile] = useState<File | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const f = new FormData();
    f.append('name', formData.name || '');
    f.append('description', formData.description || '');
    f.append('subscription_type', formData.subscription_type || 'monthly');
    f.append('price', String(formData.price || 0));
    f.append('commission_percent', String(formData.commission_percent || 0));
    f.append('risk_level', formData.risk_level || 'medium');
    f.append('platform_type', platformType);
    f.append('money_manager_name', formData.money_manager_name || '');

    if (platformType === 'mt4') {
      f.append('mt4_login', formData.mt4_login || '');
      f.append('mt4_password', formData.mt4_password || '');
      f.append('mt4_server', formData.mt4_server || '');
    } else {
      f.append('mt5_login', formData.mt5_login || '');
      f.append('mt5_password', formData.mt5_password || '');
      f.append('mt5_server', formData.mt5_server || '');
      f.append('execution_type', formData.execution_type || 'sequential');
    }
    if (logoFile) f.append('logo', logoFile);
    if (robotFile) f.append('robot_file', robotFile);
    if (settingsFile) f.append('settings_file', settingsFile);
    onSubmit(f);
  };

  const handleChange = (field: keyof CreateStrategyFormData, value: string | number) => {
    setFormData({ ...formData, [field]: value });
  };

  const stepClass = "w-8 h-8 bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-xl flex items-center justify-center text-sm font-bold shadow-md flex-shrink-0";
  const sectionClass = "bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-100";

  return (
    <form onSubmit={handleSubmit} className="max-w-3xl mx-auto space-y-6">
      <div className="text-center mb-2">
        <h1 className="text-3xl font-extrabold text-gray-900">Создание стратегии</h1>
        <p className="text-gray-500 mt-2">Заполните все поля, чтобы опубликовать торгового робота в Marketplace</p>
      </div>

      {/* Section 1 */}
      <div className={sectionClass}>
        <h2 className="text-lg font-semibold text-gray-900 mb-5 flex items-center gap-3">
          <span className={stepClass}>1</span> Основная информация
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Название стратегии *</label>
            <input type="text" required className="input-field" value={formData.name || ''}
              onChange={(e) => handleChange('name', e.target.value)} placeholder="Например: EURUSD Scalper Pro" />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Описание *</label>
            <textarea required rows={3} className="input-field" value={formData.description || ''}
              onChange={(e) => handleChange('description', e.target.value)}
              placeholder="Опишите стратегию, подход и целевую аудиторию..." />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Ваше имя (Управляющий)</label>
            <input type="text" className="input-field" value={formData.money_manager_name || ''}
              onChange={(e) => handleChange('money_manager_name', e.target.value)} placeholder="Иван Иванов" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Логотип</label>
            <input type="file" accept="image/*" className="input-field py-2"
              onChange={(e) => setLogoFile(e.target.files?.[0] || null)} />
          </div>
        </div>
      </div>

      {/* Section 2 */}
      <div className={sectionClass}>
        <h2 className="text-lg font-semibold text-gray-900 mb-5 flex items-center gap-3">
          <span className={stepClass}>2</span> Подписка и комиссия
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Тип подписки</label>
            <select className="input-field" value={formData.subscription_type}
              onChange={(e) => handleChange('subscription_type', e.target.value)}>
              <option value="daily">Ежедневно</option>
              <option value="weekly">Еженедельно</option>
              <option value="monthly">Ежемесячно</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Цена ($)</label>
            <input type="number" step="0.01" min="0" className="input-field" value={formData.price}
              onChange={(e) => handleChange('price', parseFloat(e.target.value))} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Комиссия (%)</label>
            <input type="number" step="0.1" min="0" max="100" className="input-field"
              value={formData.commission_percent}
              onChange={(e) => handleChange('commission_percent', parseFloat(e.target.value))} />
          </div>
        </div>
        <div className="mt-4 bg-blue-50 border border-blue-100 rounded-xl p-3.5 text-sm text-blue-800 flex items-center gap-2">
          <span>💡</span> Комиссия начисляется ежедневно от прибыли инвесторов
        </div>
      </div>

      {/* Section 3 */}
      <div className={sectionClass}>
        <h2 className="text-lg font-semibold text-gray-900 mb-5 flex items-center gap-3">
          <span className={stepClass}>3</span> Платформа и риск
        </h2>
        <div className="flex gap-4 mb-5">
          {(['mt4', 'mt5'] as const).map((p) => (
            <label key={p} className={`flex-1 flex items-center gap-3.5 p-4 border-2 rounded-2xl cursor-pointer transition-all
              ${platformType === p ? 'border-blue-500 bg-blue-50/50 shadow-md shadow-blue-500/10' : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'}`}>
              <input type="radio" checked={platformType === p} onChange={() => setPlatformType(p)} className="sr-only" />
              <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0
                ${platformType === p ? 'border-blue-500' : 'border-gray-300'}`}>
                {platformType === p && <div className="w-2.5 h-2.5 rounded-full bg-blue-500" />}
              </div>
              <div>
                <div className="font-bold text-gray-900">MetaTrader {p === 'mt4' ? '4' : '5'}</div>
                <div className="text-xs text-gray-500 mt-0.5">{p === 'mt4' ? '.ex4 + .set файлы' : '.ex5 + .set файлы'}</div>
              </div>
            </label>
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Уровень риска</label>
            <select className="input-field" value={formData.risk_level}
              onChange={(e) => handleChange('risk_level', e.target.value)}>
              <option value="low">Низкий</option>
              <option value="medium">Средний</option>
              <option value="high">Высокий</option>
            </select>
          </div>
          {platformType === 'mt5' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Тип исполнения</label>
              <select className="input-field" value={formData.execution_type}
                onChange={(e) => handleChange('execution_type', e.target.value)}>
                <option value="sequential">Последовательное</option>
                <option value="instant">Мгновенное</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Section 4 */}
      <div className={sectionClass}>
        <h2 className="text-lg font-semibold text-gray-900 mb-5 flex items-center gap-3">
          <span className={stepClass}>4</span> Файлы робота
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Файл робота ({platformType === 'mt4' ? '.ex4' : '.ex5'}) *
            </label>
            <input type="file" accept={platformType === 'mt4' ? '.ex4' : '.ex5'} required className="input-field py-2"
              onChange={(e) => setRobotFile(e.target.files?.[0] || null)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Файл настроек (.set)</label>
            <input type="file" accept=".set" className="input-field py-2"
              onChange={(e) => setSettingsFile(e.target.files?.[0] || null)} />
          </div>
        </div>
      </div>

      {/* Section 5 */}
      <div className={sectionClass}>
        <h2 className="text-lg font-semibold text-gray-900 mb-5 flex items-center gap-3">
          <span className={stepClass}>5</span> Подключение
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">{platformType === 'mt4' ? 'MT4' : 'MT5'} Логин *</label>
            <input type="text" required className="input-field"
              value={platformType === 'mt4' ? formData.mt4_login || '' : formData.mt5_login || ''}
              onChange={(e) => handleChange(platformType === 'mt4' ? 'mt4_login' : 'mt5_login', e.target.value)}
              placeholder="Введите логин" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">{platformType === 'mt4' ? 'MT4' : 'MT5'} Пароль *</label>
            <input type="password" required className="input-field"
              value={platformType === 'mt4' ? formData.mt4_password || '' : formData.mt5_password || ''}
              onChange={(e) => handleChange(platformType === 'mt4' ? 'mt4_password' : 'mt5_password', e.target.value)}
              placeholder="Введите пароль" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">{platformType === 'mt4' ? 'MT4' : 'MT5'} Сервер *</label>
            <input type="text" required className="input-field"
              value={platformType === 'mt4' ? formData.mt4_server || '' : formData.mt5_server || ''}
              onChange={(e) => handleChange(platformType === 'mt4' ? 'mt4_server' : 'mt5_server', e.target.value)}
              placeholder="Например: MetaQuotes-Demo" />
          </div>
        </div>
      </div>

      <button type="submit" disabled={isLoading}
        className="w-full py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-bold rounded-2xl hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 transition-all shadow-lg shadow-blue-500/25 text-base">
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
            Создание стратегии...
          </span>
        ) : '🚀 Создать стратегию'}
      </button>
    </form>
  );
};

export default StrategyForm;
