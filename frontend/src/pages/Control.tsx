import { Power, RotateCcw, Save } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { incubatorApi } from "../api/client";
import { useToast } from "../components/Toast";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input, Select } from "../components/ui/input";
import { useIncubatorStore } from "../store/incubator";
import type { RelayMode } from "../types/incubator";

export function Control() {
  const { status, loadStatus } = useIncubatorStore();
  const toast = useToast();
  const [isDirty, setIsDirty] = useState(false);
  const [hasLoadedSettings, setHasLoadedSettings] = useState(false);
  const [form, setForm] = useState({
    target_temperature: 37.5,
    target_humidity: 60,
    tolerance: 0.3,
    relay_mode: "AUTO" as RelayMode,
    manual_relay: false,
    tray_servo_enabled: false,
    tray_servo_angle: 45,
    tray_servo_interval_minutes: 120,
    tray_servo_speed_dps: 6
  });
  useEffect(() => {
    loadStatus().catch(console.error);
  }, [loadStatus]);
  useEffect(() => {
    if (status?.settings && !isDirty && !hasLoadedSettings) {
      setForm({
        target_temperature: status.settings.target_temperature,
        target_humidity: status.settings.target_humidity,
        tolerance: status.settings.tolerance,
        relay_mode: status.settings.relay_mode,
        manual_relay: status.settings.manual_relay,
        tray_servo_enabled: status.settings.tray_servo_enabled,
        tray_servo_angle: status.settings.tray_servo_angle,
        tray_servo_interval_minutes: status.settings.tray_servo_interval_minutes,
        tray_servo_speed_dps: status.settings.tray_servo_speed_dps
      });
      setHasLoadedSettings(true);
    }
  }, [hasLoadedSettings, isDirty, status]);
  const updateForm = (updates: Partial<typeof form>) => {
    setIsDirty(true);
    setForm((current) => ({ ...current, ...updates }));
  };
  const save = async (event: FormEvent) => {
    event.preventDefault();
    await incubatorApi.saveSettings({ ...form, timestamp: new Date().toISOString() });
    setIsDirty(false);
    setHasLoadedSettings(false);
    toast("Control settings saved and queued for ESP32 sync");
    await loadStatus();
  };
  const emergencyOff = async () => {
    if (!confirm("Turn the heater relay off immediately?")) return;
    await incubatorApi.relay("EMERGENCY_OFF", false, "emergency off from dashboard");
    toast("Emergency OFF command queued");
    await loadStatus();
  };
  return (
    <form className="grid gap-6 xl:grid-cols-[1fr_340px]" onSubmit={save}>
      <Card>
        <CardHeader>
          <CardTitle>Incubation Control</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <label className="space-y-2 text-sm">
            Target temperature
            <Input type="number" step="0.1" value={form.target_temperature} onChange={(e) => updateForm({ target_temperature: Number(e.target.value) })} />
          </label>
          <label className="space-y-2 text-sm">
            Target humidity
            <Input type="number" step="0.1" value={form.target_humidity} onChange={(e) => updateForm({ target_humidity: Number(e.target.value) })} />
          </label>
          <label className="space-y-2 text-sm">
            Tolerance
            <Input type="number" step="0.1" value={form.tolerance} onChange={(e) => updateForm({ tolerance: Number(e.target.value) })} />
          </label>
          <label className="space-y-2 text-sm">
            Relay mode
            <Select value={form.relay_mode} onChange={(e) => updateForm({ relay_mode: e.target.value as RelayMode })}>
              <option value="AUTO">Auto</option>
              <option value="MANUAL">Manual</option>
              <option value="EMERGENCY_OFF">Emergency OFF</option>
            </Select>
          </label>
          <label className="flex items-center gap-3 rounded-md border border-border p-3 text-sm">
            <input type="checkbox" checked={form.manual_relay} onChange={(e) => updateForm({ manual_relay: e.target.checked })} />
            Manual relay ON
          </label>
          <div className="sm:col-span-2 flex flex-wrap gap-3">
            <Button type="submit">
              <Save size={18} /> Save
            </Button>
            <Button type="button" className="bg-destructive" onClick={emergencyOff}>
              <Power size={18} /> Emergency OFF
            </Button>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Egg Tray Rotation</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <label className="flex items-center gap-3 rounded-md border border-border p-3 text-sm">
            <input type="checkbox" checked={form.tray_servo_enabled} onChange={(e) => updateForm({ tray_servo_enabled: e.target.checked })} />
            Enable tray servo
          </label>
          <label className="space-y-2 text-sm">
            Tilt angle each side
            <Input type="number" min="0" max="180" step="1" value={form.tray_servo_angle} onChange={(e) => updateForm({ tray_servo_angle: Number(e.target.value) })} />
          </label>
          <label className="space-y-2 text-sm">
            Rotation interval
            <Input type="number" min="1" max="720" step="1" value={form.tray_servo_interval_minutes} onChange={(e) => updateForm({ tray_servo_interval_minutes: Number(e.target.value) })} />
          </label>
          <label className="space-y-2 text-sm">
            Gentle speed
            <Input type="number" min="1" max="30" step="1" value={form.tray_servo_speed_dps} onChange={(e) => updateForm({ tray_servo_speed_dps: Number(e.target.value) })} />
          </label>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Active Limits</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>Lower limit: {(form.target_temperature - form.tolerance).toFixed(1)} C</p>
          <p>Upper limit: {(form.target_temperature + form.tolerance).toFixed(1)} C</p>
          <p>Auto relay: ON below lower, OFF above upper</p>
          <p>Current relay: {status?.environment?.relay ? "ON" : "OFF"}</p>
          <p>Fan relay GPIO23: {status?.environment?.fan_relay ? "ON" : "OFF"}</p>
          <p>Fan rule: ON above target humidity, otherwise follows heater relay</p>
          <p>Tray servo: {form.tray_servo_enabled ? "Enabled" : "Disabled"}</p>
          <p>Cycle: +{form.tray_servo_angle} deg to 0 deg to -{form.tray_servo_angle} deg</p>
          <p>Interval: {form.tray_servo_interval_minutes} min</p>
          <p>Speed: {form.tray_servo_speed_dps} deg/sec</p>
          <p className="inline-flex items-center gap-2"><RotateCcw size={16} /> GPIO18 Futaba S3003</p>
        </CardContent>
      </Card>
    </form>
  );
}
