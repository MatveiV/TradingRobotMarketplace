export interface Strategy {
  id: number;
  name: string;
  description: string;
  subscription_type: 'daily' | 'weekly' | 'monthly';
  price: number;
  commission_percent: number;
  risk_level: 'low' | 'medium' | 'high';
  platform_type: 'mt4' | 'mt5';
  logo_path?: string;
  status: string;
  money_manager_name?: string;
  investors_count: number;
  aum: number;
  performance_data?: PerformanceData;
  created_at: string;
  updated_at: string;
}

export interface PerformanceData {
  total_profit: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  trades: Trade[];
}

export interface Trade {
  id: string | number;
  symbol: string;
  type: 'buy' | 'sell';
  volume?: number;
  profit?: number;
  realized_pnl?: number;
  timestamp: string;
}

export interface MarketplaceStrategy {
  id: number;
  name: string;
  profit_percent: number;
  risk_level: string;
  commission_percent: number;
  platform: string;
  investors_count: number;
  aum: number;
  mm_name: string;
  logo_path?: string;
}

export interface CreateStrategyFormData {
  name: string;
  description: string;
  subscription_type: string;
  price: number;
  commission_percent: number;
  risk_level: string;
  platform_type: 'mt4' | 'mt5';
  money_manager_name?: string;
  mt4_login?: string;
  mt4_password?: string;
  mt4_server?: string;
  mt5_login?: string;
  mt5_password?: string;
  mt5_server?: string;
  execution_type?: string;
  logo?: File;
  robot_file?: File;
  settings_file?: File;
}
