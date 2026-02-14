import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useDashboardStore } from "../store";
import { StockSelector } from "../components/dashboard/StockSelector";
import { SentimentTrendChart } from "../components/charts/SentimentTrendChart";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import apiClient from "../api/client";

export function HistoricalPage() {
  const selectedTicker = useDashboardStore((s) => s.selectedTicker);
  const [days, setDays] = useState(7);

  const { data, isLoading } = useQuery({
    queryKey: ["historical", selectedTicker, days],
    queryFn: async () => {
      const from = new Date(Date.now() - days * 86400000).toISOString();
      const to = new Date().toISOString();
      const resolution = days <= 1 ? "15m" : days <= 7 ? "1h" : "4h";
      const { data } = await apiClient.get(`/historical/${selectedTicker}`, {
        params: { from, to, resolution },
      });
      return data;
    },
    enabled: !!selectedTicker,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-[var(--color-text-primary)]">
          Historical Analysis
        </h2>
        <StockSelector />
      </div>

      {selectedTicker && (
        <div className="flex gap-2">
          {[1, 7, 30, 90].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                days === d
                  ? "bg-blue-600 text-white"
                  : "bg-[var(--color-bg-card)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
              }`}
            >
              {d === 1 ? "24h" : `${d}d`}
            </button>
          ))}
        </div>
      )}

      {!selectedTicker && (
        <p className="py-12 text-center text-[var(--color-text-secondary)]">
          Select a stock to view historical data
        </p>
      )}

      {isLoading && <LoadingSpinner />}

      {data && (
        <SentimentTrendChart
          data={data.data}
          title={`${selectedTicker} Historical (${data.resolution} resolution, ${data.data_points} points)`}
        />
      )}
    </div>
  );
}
