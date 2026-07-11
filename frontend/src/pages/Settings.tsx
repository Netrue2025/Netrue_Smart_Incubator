import { RotateCcw, Save, Upload } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { getApiBaseUrl, getStoredApiBaseUrl, incubatorApi, normalizeApiBaseUrl, setApiBaseUrl } from "../api/client";
import { useToast } from "../components/Toast";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { useIncubatorStore } from "../store/incubator";

export function Settings() {
  const { status, loadStatus } = useIncubatorStore();
  const toast = useToast();
  const [form, setForm] = useState({
    device_name: "",
    timezone: "Africa/Lagos",
    sampling_interval: 1,
    sync_interval: 10,
    temperature_offset: 0,
    humidity_offset: 0
  });
  const [apiBaseInput, setApiBaseInput] = useState(() => getStoredApiBaseUrl());
  useEffect(() => {
    loadStatus().catch(console.error);
  }, [loadStatus]);
  useEffect(() => {
    if (status?.settings) setForm(status.settings);
  }, [status]);
  const save = async (event: FormEvent) => {
    event.preventDefault();
    await incubatorApi.saveSettings({ ...form, timestamp: new Date().toISOString() });
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
