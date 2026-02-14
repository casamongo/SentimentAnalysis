import { format, formatDistanceToNow } from "date-fns";

export function formatScore(score: number): string {
  const sign = score >= 0 ? "+" : "";
  return `${sign}${score.toFixed(3)}`;
}

export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatDelta(delta: number | null): string {
  if (delta === null) return "--";
  const sign = delta >= 0 ? "+" : "";
  return `${sign}${delta.toFixed(4)}`;
}

export function formatTimestamp(iso: string): string {
  return format(new Date(iso), "MMM d, HH:mm");
}

export function formatTimeAgo(iso: string): string {
  return formatDistanceToNow(new Date(iso), { addSuffix: true });
}
