import { useState } from "react";
import { Link } from "wouter";
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search } from "lucide-react";
import { useListStrategies } from "@/lib/api-client/api";
import { LineChart, Line, ResponsiveContainer } from "recharts";

export default function StrategiesTab() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const { data, isLoading } = useListStrategies({
    search: search || undefined,
    page,
    pageSize,
  });

  const strategies = data?.strategies ?? [];
  const total = data?.total ?? 0;
  const totalPages = data?.totalPages ?? 1;

  const handleSearch = (val: string) => {
    setSearch(val);
    setPage(1);
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <div className="relative w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="Search strategies..." 
            className="pl-9 bg-gray-50/50"
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="border rounded-md">
        <Table>
          <TableHeader>
            <TableRow className="bg-gray-50/50 hover:bg-gray-50/50">
              <TableHead className="w-[250px]">Strategy</TableHead>
              <TableHead className="text-right">Growth</TableHead>
              <TableHead className="text-right">Chart</TableHead>
              <TableHead className="text-right">Min Invest</TableHead>
              <TableHead className="text-right">Investors</TableHead>
              <TableHead className="text-right">Funds</TableHead>
              <TableHead className="text-right">Days</TableHead>
              <TableHead className="text-right">Fee</TableHead>
              <TableHead></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                  Loading strategies...
                </TableCell>
              </TableRow>
            ) : strategies.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                  No strategies found.
                </TableCell>
              </TableRow>
            ) : (
              strategies.map((strategy) => (
                <TableRow key={strategy.id} className="hover:bg-gray-50/30">
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-3">
                      {strategy.logoUrl ? (
                        <img src={strategy.logoUrl} alt={strategy.name} className="w-8 h-8 rounded-full bg-gray-100" />
                      ) : (
                        <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-xs font-medium text-gray-500">
                          {strategy.name.substring(0, 2).toUpperCase()}
                        </div>
                      )}
                      {strategy.name}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                      strategy.growthPercent >= 0 
                        ? 'bg-positive/10 text-positive' 
                        : 'bg-destructive/10 text-destructive'
                    }`}>
                      {strategy.growthPercent > 0 ? '+' : ''}{strategy.growthPercent}%
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="h-[40px] w-[80px] ml-auto">
                      {strategy.chartPoints && strategy.chartPoints.length > 0 && (
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={strategy.chartPoints.map((val, i) => ({ value: val, index: i }))}>
                            <Line 
                              type="monotone" 
                              dataKey="value" 
                              stroke={strategy.growthPercent >= 0 ? 'var(--color-positive)' : 'var(--color-destructive)'} 
                              strokeWidth={1.5}
                              dot={false}
                              isAnimationActive={false}
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">${strategy.minInvest}</TableCell>
                  <TableCell className="text-right">{strategy.investors}</TableCell>
                  <TableCell className="text-right">${strategy.totalFunds.toLocaleString()}</TableCell>
                  <TableCell className="text-right">{strategy.days}</TableCell>
                  <TableCell className="text-right">{strategy.performanceFee}%</TableCell>
                  <TableCell className="text-right">
                    <Link href={`/strategy/${strategy.id}`}>
                      <Button variant="default" size="sm" className="bg-[#111111] hover:bg-black/90">
                        Details
                      </Button>
                    </Link>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-1.5 mt-6">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</Button>
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
            <Button
              key={p}
              variant={p === page ? "default" : "outline"}
              size="sm"
              className={p === page ? "bg-[#111] text-white" : ""}
              onClick={() => setPage(p)}
            >
              {p}
            </Button>
          ))}
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>Next</Button>
        </div>
      )}
    </div>
  );
}
