import { BatteryCharging, Save, Zap } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { incubatorApi } from "../api/client";
import { useToast } from "../components/Toast";
import { StatusCard } from "../components/StatusCard";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Skeleton } from "../components/ui/skeleton";
import type { PowerSummary } from "../types/incubator";

export function PowerManagement() {
  const toast = useToast();
  const [data, setData] = useState<PowerSummary | null>(null);
  const [form, setForm] = useState<PowerSummary["config"] | null>(null);

  const load = async () => {
    const payload = await incubatorApi.power();
    setData(payload);
    setForm(payload.config);
  };

  useEffect(() => {
    load().catch(console.error);
  }, []);

  const save = async (event: FormEvent) => {
    event.preventDefault();
    if (!form) return;
    const payload = await incubatorApi.savePower(form);
    setData(payload);
    setForm(payload.config);
    toast("Power settings saved");
  };

  if (!data || !form) return <Skeleton className="h-[70vh] w-full" />;

  return (
    <form className="space-y-6" onSubmit={save}>
      <div className="grid gap-4 md:grid-cols-4">
        <StatusCard label="Energy 24h" value={`${data.total_kwh} kWh`} icon={<Zap />} />
        <StatusCard label="Estimated Cost" value={data.estimated_cost.toFixed(2)} />
        <StatusCard label="Current Draw" value={`${data.estimated_current_amps} A`} icon={<BatteryCharging />} />
        <StatusCard label="Heater Runtime" value={`${data.heater_runtime_minutes} min`} />
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Power Estimate Breakdown</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-3">
          <StatusCard label="Heater" value={`${data.heater_kwh} kWh`} />
          <StatusCard label="Fan + Controller" value={`${data.base_kwh} kWh`} />
          <StatusCard label="Servo" value={`${data.servo_kwh} kWh`} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Power Configuration</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <label className="space-y-2 text-sm">Heater watts<Input type="number" step="0.1" value={form.heater_watts} onChange={(event) => setForm({ ...form, heater_watts: Number(event.target.value) })} /></label>
          <label className="space-y-2 text-sm">Fan watts<Input type="number" step="0.1" value={form.fan_watts} onChange={(event) => setForm({ ...form, fan_watts: Number(event.target.value) })} /></label>
          <label className="space-y-2 text-sm">Controller watts<Input type="number" step="0.1" value={form.controller_watts} onChange={(event) => setForm({ ...form, controller_watts: Number(event.target.value) })} /></label>
          <label className="space-y-2 text-sm">Servo watts<Input type="number" step="0.1" value={form.servo_watts} onChange={(event) => setForm({ ...form, servo_watts: Number(event.target.value) })} /></label>
          <label className="space-y-2 text-sm">Grid voltage<Input type="number" step="0.1" value={form.grid_voltage} onChange={(event) => setForm({ ...form, grid_voltage: Number(event.target.value) })} /></label>
          <label className="space-y-2 text-sm">Tariff per kWh<Input type="number" step="0.01" value={form.tariff_per_kwh} onChange={(event) => setForm({ ...form, tariff_per_kwh: Number(event.target.value) })} /></label>
        </CardContent>
      </Card>
      <Button type="submit"><Save size={18} /> Save Power Settings</Button>
    </form>
  );
}
