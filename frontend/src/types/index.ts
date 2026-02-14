export interface Stock {
  id: string;
  ticker: string;
  company_name: string;
  sector: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AggregateScore {
  ticker: string;
  company_name: string;
  score: number;
  confidence: number;
  sentiment_label: SentimentLabel;
  sources_available: number;
  sources_total: number;
  source_breakdown: Record<string, number>;
  weight_breakdown: Record<string, number>;
  previous_score: number | null;
  score_delta: number | null;
  computed_at: string;
}

export interface SourceScore {
  source_name: string;
  raw_score: number | null;
  normalized_score: number;
  data_points: number;
  metadata_json: Record<string, unknown>;
  fetched_at: string;
}

export interface ScoreHistoryPoint {
  score: number;
  confidence: number;
  sentiment_label: string;
  sources_available: number;
  computed_at: string;
}

export interface ScoreSummary {
  ticker: string;
  company_name: string;
  score: number;
  confidence: number;
  sentiment_label: SentimentLabel;
  score_delta: number | null;
  sources_available: number;
  computed_at: string | null;
}

export interface SourceConfig {
  source_name: string;
  display_name: string;
  weight: number;
  is_enabled: boolean;
  category: string;
  rate_limit_rpm: number;
  last_healthy_at: string | null;
}

export interface SourceHealth {
  source_name: string;
  display_name: string;
  is_enabled: boolean;
  last_healthy_at: string | null;
  is_healthy: boolean;
}

export interface DashboardData {
  ticker: string;
  company_name: string;
  current: {
    score: number | null;
    confidence: number | null;
    sentiment_label: string | null;
    score_delta: number | null;
    sources_available: number;
    sources_total: number;
    source_breakdown: Record<string, number>;
    weight_breakdown: Record<string, number>;
    computed_at: string | null;
  };
  trend: ScoreHistoryPoint[];
  sources: {
    source_name: string;
    normalized_score: number;
    data_points: number;
    fetched_at: string;
  }[];
}

export interface SSEScoreUpdate {
  event: string;
  ticker: string;
  score: string;
  confidence: string;
  label: SentimentLabel;
  sources_available: number;
  source_breakdown: Record<string, number>;
  timestamp: string;
}

export type SentimentLabel =
  | "very_bearish"
  | "bearish"
  | "neutral"
  | "bullish"
  | "very_bullish";

export type DashboardMode = "realtime" | "historical";
