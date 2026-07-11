import { create } from "zustand";
import { incubatorApi } from "../api/client";
import type { Alert, HistoryPayload, StatusSnapshot } from "../types/incubator";

interface IncubatorState {
  status: StatusSnapshot | null;
  history: HistoryPayload;
  alerts: Alert[];
  connected: boolean;
  loading: boolean;
  loadStatus: () => Promise<void>;
  loadHistory: (range?: string) => Promise<void>;
  loadAlerts: () => Promise<void>;
  connectLive: () => () => void;
  setStatus: (status: StatusSnapshot) => void;
}

function readingKey(status: StatusSnapshot) {
  const reading = status.environment;
  return reading ? `${reading.id ?? "no-id"}-${reading.created_at ?? reading.timestamp ?? ""}` : "";
}

function appendLatestReading(state: IncubatorState, status: StatusSnapshot): HistoryPayload {
  const reading = status.environment;
  if (!reading) return state.history;
  const current = state.history.readings;
  const last = current[current.length - 1];
  const lastKey = last ? `${last.id ?? "no-id"}-${last.created_at ?? last.timestamp ?? ""}` : "";
  const nextKey = readingKey(status);
  if (lastKey === nextKey) return state.history;
  return { ...state.history, readings: [...current.slice(-300), reading] };
}

export const useIncubatorStore = create<IncubatorState>((set, get) => ({
  status: null,
  history: { readings: [], relay: [] },
  alerts: [],
  connected: false,
  loading: false,
  loadStatus: async () => {
    set({ loading: true });
    const status = await incubatorApi.status();
    set((state) => ({
      status,
      history: status.environment ? appendLatestReading(state, status) : { ...state.history, readings: [] },
      loading: false
    }));
  },
  loadHistory: async (range = "today") => {
    const history = await incubatorApi.history(range);
    set({ history });
  },
  loadAlerts: async () => {
    const alerts = await incubatorApi.alerts();
    set({ alerts });
  },
  setStatus: (status) => set({ status }),
  connectLive: () => {
    const socket = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/live`);
    socket.onopen = () => set({ connected: true });
    socket.onclose = () => set({ connected: false });
    socket.onmessage = (event) => {
      const status = JSON.parse(event.data) as StatusSnapshot;
      set((state) => ({
        status,
        history: status.environment ? appendLatestReading(state, status) : { ...state.history, readings: [] }
      }));
    };
    return () => socket.close();
  }
}));
