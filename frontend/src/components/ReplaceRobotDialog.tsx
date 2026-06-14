import React, { useState, useEffect } from 'react';

interface ReplaceRobotDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  strategyId: number;
  strategyName: string;
}

interface RunningRobot {
  id: string;
  name: string;
  strategy_id: number;
}

const ReplaceRobotDialog: React.FC<ReplaceRobotDialogProps> = ({
  isOpen, onClose, onConfirm, strategyId, strategyName
}) => {
  const [runningRobot, setRunningRobot] = useState<RunningRobot | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && strategyId) checkRunningRobot();
  }, [isOpen, strategyId]);

  const checkRunningRobot = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/strategies/${strategyId}/replace-robot`, { method: 'POST' });
      const data = await response.json();
      if (data.status === 'confirmation_required') {
        setRunningRobot(data.running_robot);
      } else {
        onConfirm();
      }
    } catch {
      setError('Failed to check robot status');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/strategies/${strategyId}/confirm-replace`, { method: 'POST' });
      const data = await response.json();
      if (data.status === 'success') {
        onConfirm();
        onClose();
      } else {
        setError(data.message || 'Failed to replace robot');
      }
    } catch {
      setError('Failed to replace robot');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div className="bg-white rounded-2xl p-6 sm:p-8 max-w-md w-full shadow-2xl border border-gray-100">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold text-gray-900">Замена робота</h3>
          <button onClick={onClose} className="w-8 h-8 rounded-xl hover:bg-gray-100 flex items-center justify-center text-gray-400 transition">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-10 w-10 border-2 border-blue-600 border-t-transparent"></div>
            <span className="ml-4 text-gray-600 font-medium">Проверяем статус...</span>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 p-4 rounded-xl mb-4">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        {!loading && !error && runningRobot && (
          <div className="space-y-5">
            <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl">
              <div className="flex items-center gap-3">
                <span className="text-2xl">⚠️</span>
                <div>
                  <p className="font-bold text-amber-800">Внимание</p>
                  <p className="text-sm text-amber-700">Другой робот уже запущен на вашем аккаунте</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <span className="text-gray-500">Название:</span>
                <span className="font-semibold text-gray-900">{runningRobot.name}</span>
                <span className="text-gray-500">ID робота:</span>
                <span className="font-semibold text-gray-900">{runningRobot.id}</span>
                <span className="text-gray-500">Стратегия:</span>
                <span className="font-semibold text-gray-900">{runningRobot.strategy_id}</span>
              </div>
            </div>

            <p className="text-gray-700">
              Заменить на <span className="font-bold text-gray-900">{strategyName}</span>?
            </p>

            <div className="flex justify-end gap-3 pt-2">
              <button onClick={onClose}
                className="px-5 py-2.5 border border-gray-200 rounded-xl text-sm font-semibold text-gray-700 hover:bg-gray-50 transition">
                Отмена
              </button>
              <button onClick={handleConfirm} disabled={loading}
                className="btn-danger text-white px-5 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-50 transition shadow-lg shadow-red-500/25">
                {loading ? 'Замена...' : 'Заменить робота'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReplaceRobotDialog;
