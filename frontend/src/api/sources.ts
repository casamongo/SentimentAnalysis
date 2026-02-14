import apiClient from "./client";
import type { SourceConfig, SourceHealth } from "../types";

export async function fetchSources(): Promise<SourceConfig[]> {
  const { data } = await apiClient.get("/sources");
  return data;
}

export async function updateSource(
  sourceName: string,
  update: { weight?: number; is_enabled?: boolean },
): Promise<SourceConfig> {
  const { data } = await apiClient.patch(`/sources/${sourceName}`, update);
  return data;
}

export async function resetWeights(): Promise<SourceConfig[]> {
  const { data } = await apiClient.post("/sources/reset-weights");
  return data;
}

export async function fetchSourceHealth(): Promise<SourceHealth[]> {
  const { data } = await apiClient.get("/sources/health");
  return data;
}
