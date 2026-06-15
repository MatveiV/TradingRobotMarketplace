import { useState } from "react";
import { useRoute, Link } from "wouter";
import { useQueryClient } from "@tanstack/react-query";
import {
  useGetStrategy,
  useGetStrategyPerformance,
  getGetStrategyQueryKey,
  getGetStrategyPerformanceQueryKey,
  getListStrategyTradesQueryKey,
} from "@/lib/api-client/api";
import { customFetch } from "@/lib/api-client/custom-fetch";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { ChevronRight, ArrowUpRight, ArrowDownRight, Plug, Trash2, XCircle } from "lucide-react";
import { format } from "date-fns";
import DeployDialog from "@/components/DeployDialog";

export default function StrategyDetail() {
  const [match, params] = useRoute("/strategy/:id");
  const strategyId = params?.id ? parseInt(params.id, 10) : 0;
  const [deployOpen, setDeployOpen] = useState(false);
  const [tradePage, setTradePage] = useState(1);
  const qc = useQueryClient();

  const { data: strategy, isLoading: isStrategyLoading } = useGetStrategy(strategyId, {
    query: { enabled: !!strategyId, queryKey: getGetStrategyQueryKey(strategyId) }
  });

  const { data: performance = [], isLoading: isPerfLoading } = useGetStrategyPerformance(strategyId, {
    query: { enabled: !!strategyId, queryKey: getGetStrategyPerformanceQueryKey(strategyId) }
  });

  const pageSize = 20;
  const tradesQK = getListStrategyTradesQueryKey(strategyId);
  const fetchTrades = async (p: number) => {
    const res = await customFetch(`/api/strategies/${strategyId}/trades?page=${p}&page_size=${pageSize}`);
    return res as { trades: any[]; total: number; page: number; pageSize: number; totalPages: number };
  };
  const [tradesData, setTradesData] = useState<{ trades: any[]; total: number; page: number; pageSize: number; totalPages: number } | null>(null);
  const [tradesLoading, setTradesLoading] = useState(false);
  useState(() => {
    fetchTrades(1).then(setTradesData).finally(() => setTradesLoading(false));
  });

  const loadPage = async (p: number) => {
    setTradesLoading(true);
    setTradePage(p);
    const data = await fetchTrades(p);
    setTradesData(data);
    setTradesLoading(false);
  };

  const handleDelete = async () => {
    if (!confirm("Delete this strategy?")) return;
    try {
      await customFetch(`/api/strategies/${strategyId}`, { method: "DELETE" });
      qc.invalidateQueries({ queryKey: ["/api/strategies"] });
      qc.invalidateQueries({ queryKey: ["/api/stats"] });
      window.location.href = "/";
    } catch { }
  };

  const handleDisconnect = async () => {
    try {
      await customFetch(`/api/strategies/${strategyId}/disconnect-investor`, { method: "POST" });
      qc.invalidateQueries({ queryKey: getGetStrategyQueryKey(strategyId) });
    } catch { }
  };

  if (isStrategyLoading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }
  if (!strategy) {
    return <div className="min-h-screen flex items-center justify-center">Strategy not found</div>;
  }

  const isPositive = strategy.growthPercent >= 0;
  const isMm = true;

  return (
    <div className="min-h-screen bg-white text-foreground">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Breadcrumb + MM actions */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center text-sm text-muted-foreground">
            <Link href="/" className="hover:text-foreground transition-colors">Available Strategies</Link>
            <ChevronRight className="w-4 h-4 mx-2" />
            <span className="text-foreground">{strategy.name}</span>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="text-destructive border-destructive/30 gap-1.5" onClick={handleDisconnect}>
              <XCircle className="w-4 h-4" /> Disconnect
            </Button>
            <Button variant="outline" size="sm" className="text-destructive border-destructive/30 gap-1.5" onClick={handleDelete}>
              <Trash2 className="w-4 h-4" /> Delete
            </Button>
          </div>
        </div>

        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          {strategy.logoUrl ? (
            <img src={strategy.logoUrl} alt={strategy.name} className="w-14 h-14 rounded-full bg-gray-100" />
          ) : (
            <div className="w-14 h-14 rounded-full bg-gray-100 flex items-center justify-center text-xl font-medium text-gray-500">
              {strategy.name.substring(0, 2).toUpperCase()}
            </div>
          )}
          <div>
            <h1 className="text-3xl font-semibold">{strategy.name}</h1>
            {strategy.availability && (
              <span className="text-xs text-muted-foreground">Availability: {strategy.availability}</span>
            )}
          </div>
        </div>

        {/* Main grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
          {/* Chart */}
          <div className="lg:col-span-2 border rounded-lg p-6 bg-white shadow-sm">
            <h2 className="text-lg font-medium mb-6">Profit/Loss (%)</h2>
            <div className="h-[400px] w-full">
              {isPerfLoading ? (
                <div className="h-full flex items-center justify-center text-muted-foreground">Loading chart...</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={performance} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={isPositive ? "#1db99a" : "#ef4444"} stopOpacity={0.2} />
                        <stop offset="95%" stopColor={isPositive ? "#1db99a" : "#ef4444"} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                    <XAxis dataKey="date" tickFormatter={(v) => String(v)} axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#888' }} dy={10} interval="preserveStartEnd" />
                    <YAxis tickFormatter={(v) => `${v}%`} axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#888' }} />
                    <Tooltip formatter={(v: number) => [`${v}%`, 'P&L']} labelFormatter={(l) => String(l)} contentStyle={{ borderRadius: '8px', border: '1px solid #eaeaea' }} />
                    <Area type="monotone" dataKey="value" stroke={isPositive ? "#1db99a" : "#ef4444"} strokeWidth={2} fillOpacity={1} fill="url(#colorValue)" />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Info panel */}
          <div className="border rounded-lg bg-gray-50/30 p-6 flex flex-col shadow-sm">
            <h2 className="text-lg font-medium mb-6">Strategy Information</h2>
            <div className="grid grid-cols-2 gap-y-5 gap-x-4 mb-8 flex-grow">
              <div>
                <div className="text-xs text-muted-foreground mb-0.5">Profit/Loss (%)</div>
                <div className={`text-lg font-semibold ${isPositive ? 'text-positive' : 'text-destructive'}`}>
                  {isPositive ? '+' : ''}{strategy.growthPercent}%
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-0.5">Drawdown (%)</div>
                <div className="text-lg font-semibold">{strategy.drawdown}%</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-0.5">Min Investment ($)</div>
                <div className="text-sm font-medium">${strategy.minInvest}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-0.5">Investor's funds ($)</div>
                <div className="text-sm font-medium">${strategy.totalFunds.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-0.5">Investors</div>
                <div className="text-sm font-medium">{strategy.investors}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-0.5">Days</div>
                <div className="text-sm font-medium">{strategy.days}</div>
              </div>
              <div className="col-span-2">
                <div className="text-xs text-muted-foreground mb-0.5">Withdrawal Policy</div>
                <div className="text-sm font-medium">{strategy.withdrawalPolicy}</div>
              </div>
              {strategy.tradesHistoryFrom && (
                <div className="col-span-2">
                  <div className="text-xs text-muted-foreground mb-0.5">Trades History From</div>
                  <div className="text-sm font-medium">{strategy.tradesHistoryFrom}</div>
                </div>
              )}
              <div className="col-span-2 border-t pt-3 mt-1 space-y-2.5">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-muted-foreground">Performance Fee / Agent Reward</span>
                  <span className="font-medium">{strategy.performanceFee}% / {strategy.performanceAgentFee}%</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-muted-foreground">Subscription Fee / Agent Reward</span>
                  <span className="font-medium">${strategy.subscriptionFee} ({strategy.subscriptionFeeType}) / {strategy.subscriptionAgentFee}%</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-muted-foreground">Entry Fee / Agent Reward</span>
                  <span className="font-medium">{strategy.entryFee}% / {strategy.entryAgentFee}%</span>
                </div>
              </div>
            </div>

            <Button
              className="w-full bg-[#111111] hover:bg-black/90 py-5 text-base shadow-lg gap-2"
              onClick={() => setDeployOpen(true)}
            >
              <Plug className="w-5 h-5" />
              Connect to strategy
            </Button>
          </div>
        </div>

        {/* Trade History */}
        <div>
          <h2 className="text-2xl font-semibold mb-6">History of Past Trades</h2>
          <div className="border rounded-md">
            <Table>
              <TableHeader>
                <TableRow className="bg-gray-50/50 hover:bg-gray-50/50">
                  <TableHead>Instrument</TableHead>
                  <TableHead>Open Time</TableHead>
                  <TableHead className="text-right">Open Price</TableHead>
                  <TableHead>Close Time</TableHead>
                  <TableHead className="text-right">Close Price</TableHead>
                  <TableHead className="text-center">Type</TableHead>
                  <TableHead className="text-right">Volume</TableHead>
                  <TableHead className="text-right">Profit</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {tradesLoading ? (
                  <TableRow><TableCell colSpan={8} className="text-center py-8 text-muted-foreground">Loading trades...</TableCell></TableRow>
                ) : !tradesData || tradesData.trades.length === 0 ? (
                  <TableRow><TableCell colSpan={8} className="text-center py-8 text-muted-foreground">No past trades available.</TableCell></TableRow>
                ) : (
                  tradesData.trades.map((trade: any) => {
                    const isBuy = trade.tradeType?.toLowerCase() === 'buy';
                    const isProfitPositive = trade.profit >= 0;
                    return (
                      <TableRow key={trade.id} className="hover:bg-gray-50/30">
                        <TableCell className="font-medium">{trade.instrument}</TableCell>
                        <TableCell>{format(new Date(trade.openTime), 'yyyy-MM-dd HH:mm:ss')}</TableCell>
                        <TableCell className="text-right">{trade.openPrice.toFixed(5)}</TableCell>
                        <TableCell>{format(new Date(trade.closeTime), 'yyyy-MM-dd HH:mm:ss')}</TableCell>
                        <TableCell className="text-right">{trade.closePrice.toFixed(5)}</TableCell>
                        <TableCell className="text-center">
                          <div className="flex justify-center">
                            {isBuy ? <ArrowUpRight className="w-4 h-4 text-positive" /> : <ArrowDownRight className="w-4 h-4 text-destructive" />}
                          </div>
                        </TableCell>
                        <TableCell className="text-right">{trade.volume.toFixed(2)}</TableCell>
                        <TableCell className={`text-right font-medium ${isProfitPositive ? 'text-positive' : 'text-destructive'}`}>
                          {isProfitPositive ? '+' : ''}${Math.abs(trade.profit).toFixed(2)}
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </div>
          {/* Paginator */}
          {tradesData && tradesData.totalPages > 1 && (
            <div className="flex items-center justify-center gap-1.5 mt-6">
              <Button variant="outline" size="sm" disabled={tradePage <= 1} onClick={() => loadPage(tradePage - 1)}>Previous</Button>
              {Array.from({ length: tradesData.totalPages }, (_, i) => i + 1).map((p) => (
                <Button
                  key={p}
                  variant={p === tradePage ? "default" : "outline"}
                  size="sm"
                  className={p === tradePage ? "bg-[#111] text-white" : ""}
                  onClick={() => loadPage(p)}
                >
                  {p}
                </Button>
              ))}
              <Button variant="outline" size="sm" disabled={tradePage >= tradesData.totalPages} onClick={() => loadPage(tradePage + 1)}>Next</Button>
            </div>
          )}
        </div>
      </div>

      <DeployDialog strategyId={strategy.id} strategyName={strategy.name} open={deployOpen} onClose={() => setDeployOpen(false)} />
    </div>
  );
}
