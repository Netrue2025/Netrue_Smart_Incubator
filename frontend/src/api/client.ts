import axios from "axios";
import type {
  Alert,
  HeaterAnalytics,
  HistoryPayload,
  IncubationPayload,
  IncubationProfile,
  NotificationSettings,
  PowerSummary,
  RelayMode,
  ServoAnalytics,
  Settings,
  StatusSnapshot,
  SystemHealth,
  WifiNetwork
} from "../types/incubator";

const API_BASE_STORAGE_KEY = "smart-incubator-api-base-url";
const BUILD_API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

function browserStorage() {
  return typeof window === "undefined" ? null : window.localStorage;
}

export function normalizeApiBaseUrl(value: string) {
  const trimmed = value.trim().replace(/\/+$/, "");
  if (!trimmed) return "/api";

  if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
    const url = new URL(trimmed);
    const pathname = url.pathname.replace(/\/+$/, "");
    url.pathname = !pathname || pathname === "/" ? "/api" : pathname.endsWith("/api") ? pathname : `${pathname}/api`;
    url.search = "";
    url.hash = "";
    return url.toString().replace(/\/+$/, "");
  }

  const relative = trimmed.startsWith("/") ? trimmed : `/${trimmed}`;
  return relative.endsWith("/api") ? relative : `${relative}/api`;
}

export function getStoredApiBaseUrl() {
  return browserStorage()?.getItem(API_BASE_STORAGE_KEY) || "";
}

export function getApiBaseUrl() {
  return normalizeApiBaseUrl(getStoredApiBaseUrl() || BUILD_API_BASE_URL);
}

export function setApiBaseUrl(value: string) {
  const storage = browserStorage();
  const trimmed = value.trim();
  if (!trimmed) {
    storage?.removeItem(API_BASE_STORAGE_KEY);
  } else {
    storage?.setItem(API_BASE_STORAGE_KEY, normalizeApiBaseUrl(trimmed));
  }
  api.defaults.baseURL = getApiBaseUrl();
}

export const api = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 30000
});

export const incubatorApi = {
  status: () => api.get<StatusSnapshot>("/status").then((r) => r.data),
  liveStatus: () => api.get<StatusSnapshot>("/live/status").then((r) => r.data),
  settings: () => api.get<Settings>("/settings").then((r) => r.data),
  saveSettings: (payload: Partial<Settings> & { timestamp?: string }) => api.post<Settings>("/settings", payload).then((r) => r.data),
  wifiNetworks: () => api.get<WifiNetwork[]>("/wifi/networks").then((r) => r.data),
  requestWifiScan: () => api.post<Settings>("/wifi/scan").then((r) => r.data),
  connectWifi: (ssid: string, password: string) => api.post<Settings>("/wifi/connect", { ssid, password, timestamp: new Date().toISOString() }).then((r) => r.data),
  relay: (mode: RelayMode, relay: boolean, reason = "operator command") => api.post<Settings>("/relay", { mode, relay, reason }).then((r) => r.data),
  history: (range = "today") => api.get<HistoryPayload>("/history", { params: { range } }).then((r) => r.data),
  alerts: () => api.get<Alert[]>("/alerts").then((r) => r.data),
  ackAlert: (id: number) => api.post(`/alerts/${id}/ack`).then((r) => r.data),
  deleteAlert: (id: number) => api.delete(`/alerts/${id}`).then((r) => r.data),
  deleteAlerts: (ids: number[]) => api.post("/alerts/delete", { ids }).then((r) => r.data),
  notificationSettings: () => api.get<NotificationSettings>("/notifications").then((r) => r.data),
  saveNotificationSettings: (payload: Partial<NotificationSettings> & { telegram_bot_token?: string; smtp_password?: string }) =>
    api.post<NotificationSettings>("/notifications", payload).then((r) => r.data),
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
