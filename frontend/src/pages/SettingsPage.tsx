import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchSources, updateSource, resetWeights, fetchSourceHealth } from "../api/sources";
import { createStock, deleteStock, fetchStocks } from "../api/stocks";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { SOURCE_CATEGORIES } from "../utils/constants";
import toast from "react-hot-toast";

export function SettingsPage() {
  const queryClient = useQueryClient();

  // Sources
  const { data: sources, isLoading: sourcesLoading } = useQuery({
    queryKey: ["sources"],
    queryFn: fetchSources,
  });

  const { data: health } = useQuery({
    queryKey: ["sourceHealth"],
    queryFn: fetchSourceHealth,
    refetchInterval: 60_000,
  });

  const updateMutation = useMutation({
    mutationFn: ({ name, update }: { name: string; update: { weight?: number; is_enabled?: boolean } }) =>
      updateSource(name, update),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["sources"] }),
  });

  const resetMutation = useMutation({
    mutationFn: resetWeights,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sources"] });
      toast.success("Weights reset to defaults");
    },
  });

  // Stocks
  const { data: stocksData, isLoading: stocksLoading } = useQuery({
    queryKey: ["stocks"],
    queryFn: fetchStocks,
  });

  const [newTicker, setNewTicker] = useState("");
  const [newName, setNewName] = useState("");

  const addStockMutation = useMutation({
    mutationFn: () => createStock(newTicker, newName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["stocks"] });
      setNewTicker("");
      setNewName("");
      toast.success(`Added ${newTicker}`);
    },
    onError: () => toast.error("Failed to add stock"),
  });

  const deleteStockMutation = useMutation({
    mutationFn: deleteStock,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["stocks"] });
      toast.success("Stock removed");
    },
  });

  const healthMap = Object.fromEntries(
    (health ?? []).map((h) => [h.source_name, h]),
  );

  return (
    <div className="space-y-8">
      <h2 className="text-xl font-bold text-[var(--color-text-primary)]">Settings</h2>

      {/* Source Weights */}
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-secondary)] p-6">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-[var(--color-text-secondary)]">
            Source Weights
          </h3>
          <button
            onClick={() => resetMutation.mutate()}
            className="rounded-lg bg-[var(--color-bg-card)] px-3 py-1.5 text-xs text-[var(--color-text-secondary)] transition-colors hover:text-[var(--color-text-primary)]"
          >
            Reset to Defaults
          </button>
        </div>

        {sourcesLoading ? (
          <LoadingSpinner />
        ) : (
          <div className="mt-4 space-y-3">
            {sources?.map((s) => {
              const h = healthMap[s.source_name];
              return (
                <div
                  key={s.source_name}
                  className="flex items-center gap-4 rounded-lg bg-[var(--color-bg-card)] px-4 py-3"
                >
                  <div className="w-3 h-3 rounded-full" style={{
                    backgroundColor: h?.is_healthy ? "#22c55e" : s.is_enabled ? "#eab308" : "#6b7280",
                  }} />
                  <div className="flex-1">
                    <div className="text-sm font-medium text-[var(--color-text-primary)]">
                      {s.display_name}
                    </div>
                    <div className="text-xs text-[var(--color-text-secondary)]">
                      {SOURCE_CATEGORIES[s.source_name] ?? s.category}
                    </div>
                  </div>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={s.is_enabled}
                      onChange={(e) =>
                        updateMutation.mutate({
                          name: s.source_name,
                          update: { is_enabled: e.target.checked },
                        })
                      }
                      className="rounded"
                    />
                    <span className="text-xs text-[var(--color-text-secondary)]">
                      Enabled
                    </span>
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="range"
                      min="0"
                      max="3"
                      step="0.1"
                      value={s.weight}
                      onChange={(e) =>
                        updateMutation.mutate({
                          name: s.source_name,
                          update: { weight: parseFloat(e.target.value) },
                        })
                      }
                      className="w-24"
                    />
                    <span className="w-10 text-right text-xs font-mono text-[var(--color-text-primary)]">
                      {s.weight.toFixed(1)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Tracked Stocks */}
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-secondary)] p-6">
        <h3 className="text-sm font-medium text-[var(--color-text-secondary)]">
          Tracked Stocks
        </h3>

        <div className="mt-4 flex gap-2">
          <input
            type="text"
            placeholder="Ticker (e.g. AAPL)"
            value={newTicker}
            onChange={(e) => setNewTicker(e.target.value.toUpperCase())}
            className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] px-3 py-1.5 text-sm text-[var(--color-text-primary)] outline-none"
          />
          <input
            type="text"
            placeholder="Company name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            className="flex-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] px-3 py-1.5 text-sm text-[var(--color-text-primary)] outline-none"
          />
          <button
            onClick={() => addStockMutation.mutate()}
            disabled={!newTicker || !newName}
            className="rounded-lg bg-blue-600 px-4 py-1.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
          >
            Add
          </button>
        </div>

        {stocksLoading ? (
          <LoadingSpinner />
        ) : (
          <div className="mt-4 space-y-2">
            {stocksData?.stocks.map((s) => (
              <div
                key={s.ticker}
                className="flex items-center justify-between rounded-lg bg-[var(--color-bg-card)] px-4 py-3"
              >
                <div>
                  <span className="text-sm font-medium text-[var(--color-text-primary)]">
                    {s.ticker}
                  </span>
                  <span className="ml-2 text-sm text-[var(--color-text-secondary)]">
                    {s.company_name}
                  </span>
                </div>
                <button
                  onClick={() => deleteStockMutation.mutate(s.ticker)}
                  className="text-xs text-red-400 transition-colors hover:text-red-300"
                >
                  Remove
                </button>
              </div>
            ))}
            {(!stocksData?.stocks || stocksData.stocks.length === 0) && (
              <p className="py-4 text-center text-sm text-[var(--color-text-secondary)]">
                No stocks tracked. Add one above.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
