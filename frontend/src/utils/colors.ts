import type { SentimentLabel } from "../types";

export function scoreToColor(score: number): string {
  if (score <= -0.6) return "#ef4444"; // red-500
  if (score <= -0.2) return "#f97316"; // orange-500
  if (score < 0.2) return "#eab308"; // yellow-500
  if (score < 0.6) return "#84cc16"; // lime-500
  return "#22c55e"; // green-500
}

export function labelToColor(label: SentimentLabel): string {
  const map: Record<SentimentLabel, string> = {
    very_bearish: "#ef4444",
    bearish: "#f97316",
    neutral: "#eab308",
    bullish: "#84cc16",
    very_bullish: "#22c55e",
  };
  return map[label] ?? "#eab308";
}

export function labelToText(label: SentimentLabel): string {
  const map: Record<SentimentLabel, string> = {
    very_bearish: "Very Bearish",
    bearish: "Bearish",
    neutral: "Neutral",
    bullish: "Bullish",
    very_bullish: "Very Bullish",
  };
  return map[label] ?? "Neutral";
}
