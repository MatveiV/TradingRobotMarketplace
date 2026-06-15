import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import StrategiesTab from "@/components/StrategiesTab";
import StrategyCreateTab from "@/components/StrategyCreateTab";
import { useGetMarketStats, getListStrategiesQueryKey } from "@/lib/api-client/api";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { customFetch } from "@/lib/api-client/custom-fetch";
import { Button } from "@/components/ui/button";
import { RefreshCw, Loader } from "lucide-react";

export default function Home() {
  const { data: stats } = useGetMarketStats();
  const queryClient = useQueryClient();
  const seedMutation = useMutation({
    mutationFn: () => customFetch("/api/strategies/seed", { method: "POST" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/strategies"] });
      queryClient.invalidateQueries({ queryKey: ["/api/stats"] });
    },
  });

  return (
    <div className="min-h-screen bg-white text-foreground">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-4xl font-semibold tracking-tight">Copy Trading</h1>
          <Button
            variant="outline"
            size="sm"
            className="gap-2"
            onClick={() => seedMutation.mutate()}
            disabled={seedMutation.isPending}
          >
            {seedMutation.isPending ? (
              <Loader className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            Generate demo strategies
          </Button>
        </div>
        
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="p-4 border rounded-lg bg-gray-50/50">
              <div className="text-sm text-muted-foreground mb-1">Total Strategies</div>
              <div className="text-2xl font-medium">{stats.totalStrategies}</div>
            </div>
            <div className="p-4 border rounded-lg bg-gray-50/50">
              <div className="text-sm text-muted-foreground mb-1">Total Investors</div>
              <div className="text-2xl font-medium">{stats.totalInvestors}</div>
            </div>
            <div className="p-4 border rounded-lg bg-gray-50/50">
              <div className="text-sm text-muted-foreground mb-1">Total Funds</div>
              <div className="text-2xl font-medium">${(stats.totalFunds / 1000000).toFixed(1)}M</div>
            </div>
            <div className="p-4 border rounded-lg bg-gray-50/50">
              <div className="text-sm text-muted-foreground mb-1">Top Growth</div>
              <div className="text-2xl font-medium text-positive">+{stats.topGrowth}%</div>
            </div>
          </div>
        )}

        <Tabs defaultValue="strategies" className="w-full">
          <TabsList className="w-full justify-start border-b rounded-none h-auto p-0 bg-transparent space-x-6">
            <TabsTrigger 
              value="how-it-works"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-0 py-3 data-[state=active]:shadow-none"
            >
              How does it work
            </TabsTrigger>
            <TabsTrigger 
              value="strategies"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-0 py-3 data-[state=active]:shadow-none"
            >
              Available Strategies
            </TabsTrigger>
            <TabsTrigger 
              value="results"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-0 py-3 data-[state=active]:shadow-none"
            >
              Investment Results
            </TabsTrigger>
            <TabsTrigger 
              value="manager"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-0 py-3 data-[state=active]:shadow-none"
            >
              For Money Manager
            </TabsTrigger>
          </TabsList>
          
          <div className="mt-6">
            <TabsContent value="how-it-works">
              <div className="py-12 text-center text-muted-foreground border rounded-lg bg-gray-50/30">
                <p>Learn how to connect to top performing strategies and automate your trading.</p>
              </div>
            </TabsContent>
            
            <TabsContent value="strategies" className="m-0">
              <StrategiesTab />
            </TabsContent>
            
            <TabsContent value="results">
              <div className="py-12 text-center text-muted-foreground border rounded-lg bg-gray-50/30">
                <p>Connect to a strategy to see your investment results here.</p>
              </div>
            </TabsContent>
            
            <TabsContent value="manager" className="m-0">
              <StrategyCreateTab />
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </div>
  );
}
