import apiClient from "./client";
import type {
  AggregateScore,
  DashboardData,
  ScoreHistoryPoint,
  ScoreSummary,
  SourceScore,
} from "../types";

export async function fetchLatestScore(ticker: string): Promise<AggregateScore> {
  const { data } = await apiClient.get(`/scores/${ticker}/latest`);
  return data;
}

export async function fetchSourceScores(ticker: string): Promise<SourceScore[]> {
  const { data } = await apiClient.get(`/scores/${ticker}/sources`);
  return data;
}

export async function fetchScoreHistory(
  ticker: string,
  from?: string,
  to?: string,
  limit?: number,
): Promise<{ ticker: string; data: ScoreHistoryPoint[]; total: number }> {
  const { data } = await apiClient.get(`/scores/${ticker}/history`, {
    params: { from, to, limit },
  });
  return data;
}

export async function fetchScoreSummaries(): Promise<ScoreSummary[]> {
  const { data } = await apiClient.get("/scores/summary");
  return data;
}

export async function fetchDashboardData(
  ticker: string,
  hours?: number,
): Promise<DashboardData> {
  const { data } = await apiClient.get(`/dashboard/${ticker}`, {
    params: hours ? { hours } : undefined,
  });
  return data;
}

export async function fetchOverview(): Promise<{
  stocks: ScoreSummary[];
}> {
  const { data } = await apiClient.get("/dashboard/overview");
  return data;
}
