import axios from "axios";
import type {
  Alert,
  HeaterAnalytics,
  HistoryPayload,
  IncubationPayload,
  IncubationProfile,
  PowerSummary,
  RelayMode,
  ServoAnalytics,
  Settings,
  StatusSnapshot,
  SystemHealth
} from "../types/incubator";

export const api = axios.create({
  baseURL: "/api",
  timeout: 8000
});

export const incubatorApi = {
  status: () => api.get<StatusSnapshot>("/status").then((r) => r.data),
  settings: () => api.get<Settings>("/settings").then((r) => r.data),
  saveSettings: (payload: Partial<Settings> & { timestamp?: string }) => api.post<Settings>("/settings", payload).then((r) => r.data),
  relay: (mode: RelayMode, relay: boolean, reason = "operator command") => api.post<Settings>("/relay", { mode, relay, reason }).then((r) => r.data),
  history: (range = "today") => api.get<HistoryPayload>("/history", { params: { range } }).then((r) => r.data),
  alerts: () => api.get<Alert[]>("/alerts").then((r) => r.data),
  ackAlert: (id: number) => api.post(`/alerts/${id}/ack`).then((r) => r.data),
  calibration: (temperature_offset: number, humidity_offset: number) =>
    api.post<Settings>("/calibration", { temperature_offset, humidity_offset }).then((r) => r.data),
  restart: () => api.post("/restart").then((r) => r.data),
  ota: () => api.post("/ota").then((r) => r.data),
  system: () => api.get<Record<string, unknown>>("/system").then((r) => r.data),
  incubation: () => api.get<IncubationPayload>("/incubation").then((r) => r.data),
  saveIncubation: (payload: Partial<IncubationProfile>) => api.post<IncubationProfile>("/incubation", payload).then((r) => r.data),
  updateIncubation: (id: number, payload: Partial<IncubationProfile>) => api.patch<IncubationProfile>(`/incubation/${id}`, payload).then((r) => r.data),
  servo: () => api.get<ServoAnalytics>("/servo").then((r) => r.data),
  heater: () => api.get<HeaterAnalytics>("/heater").then((r) => r.data),
  power: () => api.get<PowerSummary>("/power").then((r) => r.data),
  savePower: (payload: PowerSummary["config"]) => api.post<PowerSummary>("/power", payload).then((r) => r.data),
  systemHealth: () => api.get<SystemHealth>("/system-health").then((r) => r.data),
  analyticsHistory: (kind: "servo" | "heater" | "power" | "alarm" | "system-health", limit = 100) =>
    api.get<{ items: unknown[] }>(`/history/${kind}`, { params: { limit } }).then((r) => r.data)
};
