import { create } from "zustand";
import type { DashboardMode, SSEScoreUpdate } from "../types";

interface DashboardState {
  mode: DashboardMode;
  selectedTicker: string | null;
  liveScores: Record<string, SSEScoreUpdate>;
  setMode: (mode: DashboardMode) => void;
  setSelectedTicker: (ticker: string | null) => void;
  updateLiveScore: (ticker: string, update: SSEScoreUpdate) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  mode: "realtime",
  selectedTicker: null,
  liveScores: {},
  setMode: (mode) => set({ mode }),
  setSelectedTicker: (ticker) => set({ selectedTicker: ticker }),
  updateLiveScore: (ticker, update) =>
    set((state) => ({
      liveScores: { ...state.liveScores, [ticker]: update },
    })),
}));
