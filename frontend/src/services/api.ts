import axios from 'axios';
import { Strategy, PerformanceData, MarketplaceStrategy } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

const jsonApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const strategiesApi = {
  create: async (formData: FormData): Promise<Strategy> => {
    const response = await api.post('/api/strategies/', formData);
    return response.data;
  },

  list: async (params?: { platform?: string; risk?: string; sort_by?: string }): Promise<Strategy[]> => {
    const response = await jsonApi.get('/api/strategies/', { params });
    return response.data;
  },

  get: async (id: number): Promise<Strategy> => {
    const response = await jsonApi.get(`/api/strategies/${id}`);
    return response.data;
  },

  getMarketplace: async (params?: { platform?: string; risk?: string; sort_by?: string }): Promise<MarketplaceStrategy[]> => {
    const response = await jsonApi.get('/api/strategies/marketplace', { params });
    return response.data;
  },

  connect: async (id: number): Promise<any> => {
    const response = await api.post(`/api/strategies/${id}/connect`);
    return response.data;
  },

  start: async (id: number): Promise<{ status: string; started: boolean }> => {
    const response = await api.post(`/api/strategies/${id}/start`);
    return response.data;
  },

  stop: async (id: number): Promise<{ status: string }> => {
    const response = await api.post(`/api/strategies/${id}/stop`);
    return response.data;
  },

  getPerformance: async (id: number): Promise<PerformanceData> => {
    const response = await jsonApi.get(`/api/strategies/${id}/performance`);
    return response.data;
  },

  getStatus: async (id: number): Promise<{ strategy_id: number; status: string; is_running: boolean }> => {
    const response = await jsonApi.get(`/api/strategies/${id}/status`);
    return response.data;
  },

  replaceRobot: async (id: number): Promise<{ status: string; running_robot?: any }> => {
    const response = await api.post(`/api/strategies/${id}/replace-robot`);
    return response.data;
  },

  confirmReplace: async (id: number): Promise<{ status: string }> => {
    const response = await api.post(`/api/strategies/${id}/confirm-replace`);
    return response.data;
  },

  submitForModeration: async (id: number): Promise<any> => {
    const response = await jsonApi.put(`/api/strategies/${id}/submit`);
    return response.data;
  },

  approve: async (id: number): Promise<any> => {
    const response = await jsonApi.put(`/api/strategies/${id}/approve`);
    return response.data;
  },

  reject: async (id: number, reason?: string): Promise<any> => {
    const response = await jsonApi.put(`/api/strategies/${id}/reject`, { reason });
    return response.data;
  },

  investorConnect: async (strategyId: number, investmentAmount?: number): Promise<any> => {
    const response = await jsonApi.post('/api/strategies/investor/connect', {
      strategy_id: strategyId,
      investment_amount: investmentAmount || 0,
    });
    return response.data;
  },

  investorDisconnect: async (connectionId: number): Promise<any> => {
    const response = await jsonApi.post(`/api/strategies/investor/disconnect/${connectionId}`);
    return response.data;
  },
};
