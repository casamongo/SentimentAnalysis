import { ArrowDown, ArrowUp, Minus } from "lucide-react";
import { scoreToColor, labelToText } from "../../utils/colors";
import { formatScore, formatDelta, formatTimeAgo } from "../../utils/formatters";
import type { SentimentLabel } from "../../types";

interface ScoreCardProps {
  score: number | null;
  confidence: number | null;
  label: SentimentLabel | null;
  delta: number | null;
  sourcesAvailable: number;
  sourcesTotal: number;
  computedAt: string | null;
}

export function ScoreCard({
  score,
  confidence,
  label,
  delta,
  sourcesAvailable,
  sourcesTotal,
  computedAt,
}: ScoreCardProps) {
  if (score === null) {
    return (
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-secondary)] p-6">
        <p className="text-center text-[var(--color-text-secondary)]">
          No score data yet. Waiting for first cycle...
        </p>
      </div>
    );
  }

  const color = scoreToColor(score);

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-secondary)] p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-[var(--color-text-secondary)]">
            Aggregate Sentiment
          </p>
          <div className="mt-2 flex items-baseline gap-3">
            <span
              className="text-4xl font-bold"
              style={{ color }}
            >
              {formatScore(score)}
            </span>
            {delta !== null && (
              <span className="flex items-center gap-1 text-sm" style={{ color: delta >= 0 ? "#22c55e" : "#ef4444" }}>
                {delta > 0 ? <ArrowUp className="h-3 w-3" /> : delta < 0 ? <ArrowDown className="h-3 w-3" /> : <Minus className="h-3 w-3" />}
                {formatDelta(delta)}
              </span>
            )}
          </div>
          {label && (
            <span
              className="mt-2 inline-block rounded-full px-3 py-1 text-xs font-medium"
              style={{ backgroundColor: `${color}20`, color }}
            >
              {labelToText(label)}
            </span>
          )}
        </div>

        <div className="text-right">
          <div className="text-xs text-[var(--color-text-secondary)]">
            Confidence
          </div>
          <div className="mt-1 text-lg font-semibold text-[var(--color-text-primary)]">
            {confidence !== null ? `${(confidence * 100).toFixed(0)}%` : "--"}
          </div>
          <div className="mt-2 text-xs text-[var(--color-text-secondary)]">
            {sourcesAvailable}/{sourcesTotal} sources
          </div>
          {computedAt && (
            <div className="mt-1 text-xs text-[var(--color-text-secondary)]">
              {formatTimeAgo(computedAt)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
