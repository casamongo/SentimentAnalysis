import { useQuery } from "@tanstack/react-query";
import { fetchStocks } from "../../api/stocks";
import { useDashboardStore } from "../../store";

export function StockSelector() {
  const selectedTicker = useDashboardStore((s) => s.selectedTicker);
  const setSelectedTicker = useDashboardStore((s) => s.setSelectedTicker);

  const { data } = useQuery({
    queryKey: ["stocks"],
    queryFn: fetchStocks,
    refetchInterval: 60_000,
  });

  const stocks = data?.stocks ?? [];

  return (
    <div className="flex items-center gap-2">
      <label className="text-sm text-[var(--color-text-secondary)]">Stock:</label>
      <select
        value={selectedTicker ?? ""}
        onChange={(e) => setSelectedTicker(e.target.value || null)}
        className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] px-3 py-1.5 text-sm text-[var(--color-text-primary)] outline-none focus:border-blue-500"
      >
        <option value="">Select a stock...</option>
        {stocks.map((s) => (
          <option key={s.ticker} value={s.ticker}>
            {s.ticker} - {s.company_name}
          </option>
        ))}
      </select>
    </div>
  );
}
