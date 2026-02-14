import { useEffect, useRef, useCallback } from "react";
import { useDashboardStore } from "../store";
import type { SSEScoreUpdate } from "../types";

export function useSSE(tickers: string[]) {
  const eventSourceRef = useRef<EventSource | null>(null);
  const updateLiveScore = useDashboardStore((s) => s.updateLiveScore);

  const connect = useCallback(() => {
    if (tickers.length === 0) return;

    const params = new URLSearchParams();
    tickers.forEach((t) => params.append("tickers", t));

    const es = new EventSource(`/api/v1/sse/scores?${params.toString()}`);

    es.addEventListener("score_update", (event) => {
      const data: SSEScoreUpdate = JSON.parse(event.data);
      updateLiveScore(data.ticker, data);
    });

    es.onerror = () => {
      es.close();
      setTimeout(connect, 5000);
    };

    eventSourceRef.current = es;
  }, [tickers, updateLiveScore]);

  useEffect(() => {
    connect();
    return () => {
      eventSourceRef.current?.close();
    };
  }, [connect]);
}
