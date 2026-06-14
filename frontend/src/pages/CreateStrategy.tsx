import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import StrategyForm from '../components/StrategyForm';
import ReplaceRobotDialog from '../components/ReplaceRobotDialog';
import { strategiesApi } from '../services/api';

const CreateStrategy: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showReplaceDialog, setShowReplaceDialog] = useState(false);
  const [createdStrategy, setCreatedStrategy] = useState<any>(null);
  const [strategyName, setStrategyName] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (formData: FormData) => {
    setIsLoading(true);
    setError(null);
    try {
      const strategyNameValue = formData.get('name') as string;
      setStrategyName(strategyNameValue);
      const strategy = await strategiesApi.create(formData);
      setCreatedStrategy(strategy);
      const replaceResponse = await fetch(`/api/strategies/${strategy.id}/replace-robot`, { method: 'POST' });
      const replaceData = await replaceResponse.json();
      if (replaceData.status === 'confirmation_required') {
        setShowReplaceDialog(true);
      } else {
        await connectAndStart(strategy.id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to create strategy');
    } finally {
      setIsLoading(false);
    }
  };

  const connectAndStart = async (strategyId: number) => {
    try {
      await strategiesApi.connect(strategyId);
      await strategiesApi.start(strategyId);
      navigate(`/strategies/${strategyId}`);
    } catch (err: any) {
      setError(err.message || 'Failed to connect strategy');
    }
  };

  const handleReplaceConfirm = async () => {
    if (!createdStrategy) return;
    try {
      await fetch(`/api/strategies/${createdStrategy.id}/confirm-replace`, { method: 'POST' });
      await connectAndStart(createdStrategy.id);
    } catch (err: any) {
      setError(err.message || 'Failed to replace robot');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 py-8 sm:py-12 px-4">
      {error && (
        <div className="max-w-3xl mx-auto mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm flex items-center gap-2">
          <span>⚠️</span> {error}
        </div>
      )}
      <StrategyForm onSubmit={handleSubmit} isLoading={isLoading} />
      <ReplaceRobotDialog
        isOpen={showReplaceDialog}
        onClose={() => setShowReplaceDialog(false)}
        onConfirm={handleReplaceConfirm}
        strategyId={createdStrategy?.id || 0}
        strategyName={strategyName}
      />
    </div>
  );
};

export default CreateStrategy;
