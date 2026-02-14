import { useQuery } from "@tanstack/react-query";
import { useDashboardStore } from "../store";
import { fetchDashboardData, fetchScoreSummaries } from "../api/scores";
import { useSSE } from "../hooks/useSSE";
import { ScoreCard } from "../components/dashboard/ScoreCard";
import { StockSelector } from "../components/dashboard/StockSelector";
import { SentimentTrendChart } from "../components/charts/SentimentTrendChart";
import { SourceBreakdownChart } from "../components/charts/SourceBreakdownChart";
import { SourceList } from "../components/sources/SourceList";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { scoreToColor } from "../utils/colors";
import { formatScore, labelToText } from "../utils/colors";
import type { SentimentLabel } from "../types";

export function DashboardPage() {
  const selectedTicker = useDashboardStore((s) => s.selectedTicker);
  const mode = useDashboardStore((s) => s.mode);

  // Subscribe to SSE updates for the selected ticker
  useSSE(selectedTicker ? [selectedTicker] : []);

  // Fetch summaries for the overview table
  const { data: summaries, isLoading: summariesLoading } = useQuery({
    queryKey: ["summaries"],
    queryFn: fetchScoreSummaries,
    refetchInterval: 60_000,
  });

  // Fetch full dashboard data for the selected ticker
  const { data: dashboard, isLoading: dashboardLoading } = useQuery({
    queryKey: ["dashboard", selectedTicker],
    queryFn: () => fetchDashboardData(selectedTicker!, mode === "historical" ? 168 : 24),
    enabled: !!selectedTicker,
    refetchInterval: 60_000,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-[var(--color-text-primary)]">
          Dashboard
        </h2>
        <StockSelector />
      </div>

      {/* Overview table when no stock selected */}
      {!selectedTicker && (
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-secondary)] p-4">
          <h3 className="mb-4 text-sm font-medium text-[var(--color-text-secondary)]">
            All Tracked Stocks
          </h3>
          {summariesLoading ? (
            <LoadingSpinner />
          ) : summaries && summaries.length > 0 ? (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--color-border)] text-left text-xs text-[var(--color-text-secondary)]">
                  <th className="pb-2">Ticker</th>
                  <th className="pb-2">Company</th>
                  <th className="pb-2 text-right">Score</th>
                  <th className="pb-2 text-right">Confidence</th>
                  <th className="pb-2 text-right">Sentiment</th>
                  <th className="pb-2 text-right">Sources</th>
                </tr>
              </thead>
              <tbody>
                {summaries.map((s) => (
                  <tr
                    key={s.ticker}
                    className="cursor-pointer border-b border-[var(--color-border)]/50 transition-colors hover:bg-[var(--color-bg-card)]"
                    onClick={() =>
                      useDashboardStore.getState().setSelectedTicker(s.ticker)
                    }
                  >
                    <td className="py-3 font-medium text-[var(--color-text-primary)]">
                      {s.ticker}
                    </td>
                    <td className="py-3 text-[var(--color-text-secondary)]">
                      {s.company_name}
                    </td>
                    <td className="py-3 text-right font-mono" style={{ color: scoreToColor(s.score) }}>
                      {s.score !== 0 ? formatScoreVal(s.score) : "--"}
                    </td>
                    <td className="py-3 text-right text-[var(--color-text-secondary)]">
                      {s.confidence ? `${(s.confidence * 100).toFixed(0)}%` : "--"}
                    </td>
                    <td className="py-3 text-right">
                      <span
                        className="rounded-full px-2 py-0.5 text-xs"
                        style={{
                          backgroundColor: `${scoreToColor(s.score)}20`,
                          color: scoreToColor(s.score),
                        }}
                      >
                        {labelToTextVal(s.sentiment_label)}
                      </span>
                    </td>
                    <td className="py-3 text-right text-[var(--color-text-secondary)]">
                      {s.sources_available}/13
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="py-8 text-center text-[var(--color-text-secondary)]">
              No stocks tracked yet. Add stocks in Settings.
            </p>
          )}
        </div>
      )}

      {/* Selected stock dashboard */}
      {selectedTicker && dashboardLoading && <LoadingSpinner />}

      {selectedTicker && dashboard && (
        <>
          <ScoreCard
            score={dashboard.current.score}
            confidence={dashboard.current.confidence}
            label={dashboard.current.sentiment_label as SentimentLabel | null}
            delta={dashboard.current.score_delta}
            sourcesAvailable={dashboard.current.sources_available}
            sourcesTotal={dashboard.current.sources_total}
            computedAt={dashboard.current.computed_at}
          />

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <SentimentTrendChart
              data={dashboard.trend}
              title={`${selectedTicker} Sentiment Trend (${mode === "historical" ? "7d" : "24h"})`}
            />
            <SourceBreakdownChart breakdown={dashboard.current.source_breakdown} />
          </div>

          <SourceList sources={dashboard.sources} />
        </>
      )}
    </div>
  );
}

function formatScoreVal(score: number): string {
  const sign = score >= 0 ? "+" : "";
  return `${sign}${score.toFixed(3)}`;
}

function labelToTextVal(label: string): string {
  const map: Record<string, string> = {
    very_bearish: "Very Bearish",
    bearish: "Bearish",
    neutral: "Neutral",
    bullish: "Bullish",
    very_bullish: "Very Bullish",
  };
  return map[label] ?? "Neutral";
}
