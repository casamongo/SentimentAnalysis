import { scoreToColor } from "../../utils/colors";
import { SOURCE_DISPLAY_NAMES, SOURCE_CATEGORIES } from "../../utils/constants";
import { formatScore } from "../../utils/formatters";

interface SourceListProps {
  sources: {
    source_name: string;
    normalized_score: number;
    data_points: number;
    fetched_at: string;
  }[];
}

export function SourceList({ sources }: SourceListProps) {
  if (sources.length === 0) {
    return (
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-secondary)] p-4">
        <h3 className="mb-4 text-sm font-medium text-[var(--color-text-secondary)]">
          Sources
        </h3>
        <p className="py-4 text-center text-sm text-[var(--color-text-secondary)]">
          No source data available
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-secondary)] p-4">
      <h3 className="mb-4 text-sm font-medium text-[var(--color-text-secondary)]">
        Sources ({sources.length}/13)
      </h3>
      <div className="space-y-2">
        {sources.map((s) => (
          <div
            key={s.source_name}
            className="flex items-center justify-between rounded-lg bg-[var(--color-bg-card)] px-4 py-3"
          >
            <div>
              <span className="text-sm font-medium text-[var(--color-text-primary)]">
                {SOURCE_DISPLAY_NAMES[s.source_name] ?? s.source_name}
              </span>
              <span className="ml-2 text-xs text-[var(--color-text-secondary)]">
                {SOURCE_CATEGORIES[s.source_name] ?? ""}
              </span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-xs text-[var(--color-text-secondary)]">
                {s.data_points} pts
              </span>
              <span
                className="text-sm font-mono font-semibold"
                style={{ color: scoreToColor(s.normalized_score) }}
              >
                {formatScore(s.normalized_score)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
