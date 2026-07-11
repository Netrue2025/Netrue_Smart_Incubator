import { RotateCcw, Save, Search, Upload, Wifi } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { getApiBaseUrl, getStoredApiBaseUrl, incubatorApi, normalizeApiBaseUrl, setApiBaseUrl } from "../api/client";
import { useToast } from "../components/Toast";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { useIncubatorStore } from "../store/incubator";
import type { WifiNetwork } from "../types/incubator";

export function Settings() {
  const { status, loadStatus } = useIncubatorStore();
  const toast = useToast();
  const [form, setForm] = useState({
    device_name: "",
    timezone: "Africa/Lagos",
    sampling_interval: 1,
    sync_interval: 10,
    temperature_offset: 0,
    humidity_offset: 0,
    wifi_ssid: "",
    wifi_password_set: false,
    wifi_scan_requested: false,
    wifi_connect_requested: false,
    wifi_active_ssid: "",
    wifi_ip_address: "",
    wifi_rssi: null as number | null,
    wifi_connection_status: "not_configured",
    wifi_last_scan_at: null as string | null,
    wifi_last_connect_at: null as string | null
  });
  const [apiBaseInput, setApiBaseInput] = useState(() => getStoredApiBaseUrl());
  const [wifiNetworks, setWifiNetworks] = useState<WifiNetwork[]>([]);
  const [wifiPassword, setWifiPassword] = useState("");
  useEffect(() => {
    loadStatus().catch(console.error);
    incubatorApi.wifiNetworks().then(setWifiNetworks).catch(console.error);
  }, [loadStatus]);
  useEffect(() => {
    if (status?.settings) {
      setForm({ ...status.settings, wifi_ip_address: status.settings.wifi_ip_address ?? "", wifi_active_ssid: status.settings.wifi_active_ssid ?? "", wifi_ssid: status.settings.wifi_ssid ?? "" });
    }
  }, [status]);
  const save = async (event: FormEvent) => {
    event.preventDefault();
    await incubatorApi.saveSettings({
      device_name: form.device_name,
      timezone: form.timezone,
      sampling_interval: form.sampling_interval,
      sync_interval: form.sync_interval,
      temperature_offset: form.temperature_offset,
      humidity_offset: form.humidity_offset,
      timestamp: new Date().toISOString()
    });
    toast("Settings saved");
    await loadStatus();
  };
  const restart = async () => {
    if (!confirm("Restart the ESP32 when it next syncs?")) return;
    await incubatorApi.restart();
    toast("Restart command queued");
  };
  const saveConnection = async () => {
    setApiBaseUrl(apiBaseInput);
    toast("Backend connection saved");
    window.setTimeout(() => window.location.reload(), 400);
  };
  const requestWifiScan = async () => {
    await incubatorApi.requestWifiScan();
    toast("WiFi scan requested; wait for the ESP32 to sync");
    await loadStatus();
  };
  const refreshWifiNetworks = async () => {
    const networks = await incubatorApi.wifiNetworks();
    setWifiNetworks(networks);
    toast("WiFi scan results refreshed");
  };
  const saveWifi = async () => {
    if (!form.wifi_ssid.trim()) {
      toast("Choose or type a WiFi network name");
      return;
    }
    await incubatorApi.connectWifi(form.wifi_ssid.trim(), wifiPassword);
    setWifiPassword("");
    toast("WiFi credentials queued for ESP32");
    await loadStatus();
  };
  return (
    <form className="space-y-6" onSubmit={save}>
      <Card>
        <CardHeader>
          <CardTitle>Dashboard Connection</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 lg:grid-cols-[1fr_auto]">
          <label className="space-y-2 text-sm">
            Backend API URL
            <Input
              placeholder="https://your-backend-domain.com"
              value={apiBaseInput}
              onChange={(e) => setApiBaseInput(e.target.value)}
            />
          </label>
          <div className="flex items-end gap-3">
            <Button type="button" onClick={saveConnection}>
              <Save size={18} /> Save Connection
            </Button>
            <Button type="button" className="border border-border bg-muted text-foreground" onClick={() => setApiBaseInput("")}>
              Local Default
            </Button>
          </div>
          <div className="rounded-md border border-border bg-muted/40 p-3 text-xs text-foreground/70 lg:col-span-2">
            Active API: {normalizeApiBaseUrl(apiBaseInput || getApiBaseUrl())}
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>ESP32 WiFi</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 lg:grid-cols-2">
          <div className="grid gap-3 rounded-md border border-border p-4 text-sm">
            <p>Status: {form.wifi_connection_status}</p>
            <p>Connected SSID: {form.wifi_active_ssid || "Waiting for ESP32 report"}</p>
            <p>IP address: {form.wifi_ip_address || "--"}</p>
            <p>Signal: {form.wifi_rssi === null ? "--" : `${form.wifi_rssi} dBm`}</p>
            <p>Scan requested: {form.wifi_scan_requested ? "Yes" : "No"}</p>
            <p>Connect queued: {form.wifi_connect_requested ? "Yes" : "No"}</p>
          </div>
          <div className="grid gap-4">
            <label className="space-y-2 text-sm">
              Available networks
              <select
                className="h-10 w-full rounded-md border border-border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-primary"
                value={form.wifi_ssid}
                onChange={(event) => setForm({ ...form, wifi_ssid: event.target.value })}
              >
                <option value="">Select or type SSID</option>
                {wifiNetworks.map((network) => (
                  <option key={`${network.ssid}-${network.last_seen_at}`} value={network.ssid}>
                    {network.ssid} ({network.rssi} dBm, {network.encryption})
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-2 text-sm">
              WiFi name
              <Input value={form.wifi_ssid} onChange={(event) => setForm({ ...form, wifi_ssid: event.target.value })} />
            </label>
            <label className="space-y-2 text-sm">
              WiFi password
              <Input type="password" value={wifiPassword} placeholder={form.wifi_password_set ? "Saved password unchanged unless replaced" : ""} onChange={(event) => setWifiPassword(event.target.value)} />
            </label>
            <div className="flex flex-wrap gap-3">
              <Button type="button" onClick={requestWifiScan}>
                <Search size={18} /> Scan
              </Button>
              <Button type="button" className="border border-border bg-muted text-foreground" onClick={refreshWifiNetworks}>
                <RotateCcw size={18} /> Refresh
              </Button>
              <Button type="button" onClick={saveWifi}>
                <Wifi size={18} /> Connect ESP32
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Device Settings</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <label className="space-y-2 text-sm">Device name<Input value={form.device_name} onChange={(e) => setForm({ ...form, device_name: e.target.value })} /></label>
          <label className="space-y-2 text-sm">Timezone<Input value={form.timezone} onChange={(e) => setForm({ ...form, timezone: e.target.value })} /></label>
          <label className="space-y-2 text-sm">Sampling interval<Input type="number" value={form.sampling_interval} onChange={(e) => setForm({ ...form, sampling_interval: Number(e.target.value) })} /></label>
          <label className="space-y-2 text-sm">Sync interval<Input type="number" value={form.sync_interval} onChange={(e) => setForm({ ...form, sync_interval: Number(e.target.value) })} /></label>
          <label className="space-y-2 text-sm">Temperature offset<Input type="number" step="0.1" value={form.temperature_offset} onChange={(e) => setForm({ ...form, temperature_offset: Number(e.target.value) })} /></label>
          <label className="space-y-2 text-sm">Humidity offset<Input type="number" step="0.1" value={form.humidity_offset} onChange={(e) => setForm({ ...form, humidity_offset: Number(e.target.value) })} /></label>
        </CardContent>
      </Card>
      <div className="flex flex-wrap gap-3">
        <Button type="submit"><Save size={18} /> Save</Button>
        <Button type="button" onClick={restart}><RotateCcw size={18} /> Restart Device</Button>
        <Button type="button" onClick={() => incubatorApi.ota().then(() => toast("OTA command queued"))}><Upload size={18} /> OTA Update</Button>
        <Button type="button" className="bg-destructive" onClick={() => confirm("Factory reset requires firmware-side confirmation on the LCD.") && toast("Factory reset is protected by firmware confirmation")}>Factory Reset</Button>
      </div>
    </form>
  );
}
