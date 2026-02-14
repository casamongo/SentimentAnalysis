import apiClient from "./client";
import type { Stock } from "../types";

export async function fetchStocks(): Promise<{ stocks: Stock[]; total: number }> {
  const { data } = await apiClient.get("/stocks", { params: { is_active: true } });
  return data;
}

export async function createStock(ticker: string, companyName: string): Promise<Stock> {
  const { data } = await apiClient.post("/stocks", {
    ticker,
    company_name: companyName,
  });
  return data;
}

export async function deleteStock(ticker: string): Promise<void> {
  await apiClient.delete(`/stocks/${ticker}`);
}
