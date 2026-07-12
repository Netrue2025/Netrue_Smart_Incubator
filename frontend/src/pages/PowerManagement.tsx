import {
  ArrowDownTrayIcon,
  Battery100Icon,
  BoltIcon,
  DocumentArrowDownIcon,
  PrinterIcon
} from "@heroicons/react/24/outline";
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip
} from "chart.js";
import type { FormEvent } from "react";
import { useEffect, useMemo, useState } from "react";
import { Bar } from "react-chartjs-2";
import { incubatorApi } from "../api/client";
import { useToast } from "../components/Toast";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input, Select } from "../components/ui/input";
import { Skeleton } from "../components/ui/skeleton";
import type { PowerSummary } from "../types/incubator";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

type PowerConfig = PowerSummary["config"];
type PartialPowerPayload = Partial<Omit<PowerSummary, "config">> & { config?: Partial<PowerConfig> };

function normalizeConfig(config: Partial<PowerConfig> = {}): PowerConfig {
  return {
    heater_watts: config.heater_watts ?? 60,
    fan_watts: config.fan_watts ?? 3,
    controller_watts: config.controller_watts ?? 1,
    servo_watts: config.servo_watts ?? 5,
    servo_average_watts: config.servo_average_watts ?? 0.1,
    lcd_watts: config.lcd_watts ?? 0.5,
    relay_watts: config.relay_watts ?? 0.4,
    dht22_watts: config.dht22_watts ?? 0.02,
    buzzer_watts: config.buzzer_watts ?? 0,
    grid_voltage: config.grid_voltage ?? 220,
    tariff_per_kwh: config.tariff_per_kwh ?? 0,
    battery_backup_enabled: config.battery_backup_enabled ?? false,
    battery_voltage: config.battery_voltage ?? 12,
    battery_capacity_ah: config.battery_capacity_ah ?? 130,
    battery_charge_percent: config.battery_charge_percent ?? 100,
    battery_health_percent: config.battery_health_percent ?? 100,
    battery_usable_percent: config.battery_usable_percent ?? 60,
    inverter_efficiency_percent: config.inverter_efficiency_percent ?? 88,
    battery_chemistry: config.battery_chemistry ?? "Gel",
    updated_at: config.updated_at ?? new Date().toISOString()
  };
}

function normalizePowerPayload(payload: PartialPowerPayload): PowerSummary {
  const config = normalizeConfig(payload.config);
  const hourly = payload.hourly_history ?? [];
  const now = new Date().toISOString();
  const nowDate = new Date(payload.rtc_time ?? now);
  const currentHourStart = new Date(nowDate);
  currentHourStart.setUTCMinutes(0, 0, 0);
  const lastCompletedHourStart = new Date(currentHourStart);
  lastCompletedHourStart.setUTCHours(lastCompletedHourStart.getUTCHours() - 1);
  const formatHour = (date: Date) => `${date.getUTCHours().toString().padStart(2, "0")}:00`;
  return {
    config,
    window_hours: payload.window_hours ?? 24,
    heater_kwh: payload.heater_kwh ?? 0,
    base_kwh: payload.base_kwh ?? 0,
    servo_kwh: payload.servo_kwh ?? 0,
    total_kwh: payload.total_kwh ?? 0,
    estimated_cost: payload.estimated_cost ?? 0,
    estimated_current_amps: payload.estimated_current_amps ?? 0,
    heater_runtime_minutes: payload.heater_runtime_minutes ?? 0,
    heater_cycles: payload.heater_cycles ?? 0,
    live_load_watts: payload.live_load_watts ?? 0,
    average_load_watts: payload.average_load_watts ?? 0,
    peak_load_watts: payload.peak_load_watts ?? 0,
    energy_last_hour_wh: payload.energy_last_hour_wh ?? 0,
    energy_current_hour_wh: payload.energy_current_hour_wh ?? 0,
    energy_today_wh: payload.energy_today_wh ?? Math.round((payload.total_kwh ?? 0) * 1000 * 100) / 100,
    heater_duty_last_hour_percent: payload.heater_duty_last_hour_percent ?? 0,
    heater_duty_current_hour_percent: payload.heater_duty_current_hour_percent ?? 0,
    last_completed_hour_start: payload.last_completed_hour_start ?? lastCompletedHourStart.toISOString(),
    last_completed_hour_end: payload.last_completed_hour_end ?? currentHourStart.toISOString(),
    last_completed_hour_label: payload.last_completed_hour_label ?? `${formatHour(lastCompletedHourStart)} - ${formatHour(currentHourStart)} GMT`,
    current_hour_start: payload.current_hour_start ?? currentHourStart.toISOString(),
    current_hour_label: payload.current_hour_label ?? `${formatHour(currentHourStart)} - ${formatHour(new Date(currentHourStart.getTime() + 60 * 60 * 1000))} GMT`,
    rtc_time: payload.rtc_time ?? now,
    battery: payload.battery ?? {
      energy_wh:
        config.battery_voltage *
        config.battery_capacity_ah *
        (config.battery_charge_percent / 100) *
        (config.battery_health_percent / 100) *
        (config.battery_usable_percent / 100) *
        (config.inverter_efficiency_percent / 100),
      runtime_hours: null,
      recharge_before: null,
      severity: "unknown",
      basis_average_watts: 0,
      sample_count: 0,
      confidence: "low"
    },
    recharge_before: payload.recharge_before ?? null,
    live: payload.live ?? {
      heater_state: "OFF",
      heater_on: false,
      heater_on_time: null,
      heater_off_time: null,
      temperature: null,
      humidity: null,
      fan_on: false,
      servo_status: "Unknown",
      servo_active: false,
      buzzer_active: false
    },
    hourly_history: hourly,
    report: payload.report ?? {
      title: "Smart Incubator Power Report",
      date: payload.rtc_time ?? now,
      battery: config,
      summary: {
        total_energy_used_wh: payload.energy_today_wh ?? 0,
        average_load_watts: payload.average_load_watts ?? 0,
        peak_load_watts: payload.peak_load_watts ?? 0,
        average_heater_duty_percent: payload.heater_duty_last_hour_percent ?? 0,
        last_hour_energy_wh: payload.energy_last_hour_wh ?? 0,
        current_hour_energy_wh: payload.energy_current_hour_wh ?? 0,
        last_completed_hour_label: payload.last_completed_hour_label,
        current_hour_label: payload.current_hour_label,
        estimated_runtime_hours: null
      },
      hourly_table: hourly
    }
  };
}

function wh(value: number) {
  if (value >= 1000) return `${(value / 1000).toFixed(2)} kWh`;
  return `${value.toFixed(1)} Wh`;
}

function gmtDayLabel(value: string) {
  const date = new Date(value);
  return date.toLocaleDateString([], { timeZone: "UTC", year: "numeric", month: "long", day: "numeric" });
}

function runtime(hours: number | null) {
  if (hours === null || !Number.isFinite(hours)) return "--";
  return `${Math.floor(hours)}h ${Math.round((hours % 1) * 60)}m`;
}

function downloadBlob(name: string, content: string, type: string) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function PowerManagement() {
  const toast = useToast();
  const [data, setData] = useState<PowerSummary | null>(null);
  const [form, setForm] = useState<PowerConfig | null>(null);

  const load = async () => {
    const payload = normalizePowerPayload(await incubatorApi.power());
    setData(payload);
    setForm(payload.config);
  };

  useEffect(() => {
    load().catch(console.error);
  }, []);

  const save = async (event: FormEvent) => {
    event.preventDefault();
    if (!form) return;
    const payload = normalizePowerPayload(await incubatorApi.savePower(form));
    setData(payload);
    setForm(payload.config);
    toast("Power settings saved");
  };

  const chartData = useMemo(() => {
    const history = data?.hourly_history ?? [];
    return {
      labels: history.map((point) => point.hour),
      datasets: [
        {
          label: "Energy used",
          data: history.map((point) => point.energy_wh),
          backgroundColor: "rgba(20, 184, 166, 0.72)",
          borderRadius: 4
        }
      ]
    };
  }, [data]);

  if (!data || !form) return <Skeleton className="h-[70vh] w-full" />;

  const printedRows = data.hourly_history;
  const backupEnabled = data.config.battery_backup_enabled;

  const csv = () => {
    const rows = [["GMT Hour", "Power Consumption Wh"], ...printedRows.map((row) => [row.hour, row.energy_wh])];
    rows.push(["Total", data.energy_today_wh]);
    downloadBlob(`Power_Report_${new Date().toISOString().slice(0, 10)}.csv`, rows.map((row) => row.join(",")).join("\n"), "text/csv");
  };

  const printReport = () => {
    const body = printedRows
      .map((row) => {
        const isCurrent = row.hour === data.current_hour_label.slice(0, 5);
        return `<tr><td>${row.hour}${isCurrent ? " <span>(current hour so far)</span>" : ""}</td><td>${row.energy_wh.toFixed(1)} Wh</td></tr>`;
      })
      .join("");
    const win = window.open("", "_blank");
    if (!win) return;
    win.document.write(`
      <html>
        <head>
          <title>Netrue Smart Incubator Power Report</title>
          <style>
            * { box-sizing: border-box; }
            body { font-family: Arial, sans-serif; padding: 32px; color: #111827; background: #ffffff; }
            .header { border-bottom: 4px solid #0f766e; padding-bottom: 18px; margin-bottom: 24px; }
            .brand { color: #0f766e; font-size: 24px; font-weight: 800; letter-spacing: 0.02em; margin: 0; }
            .title { font-size: 18px; font-weight: 700; margin: 6px 0 0; }
            .meta { color: #4b5563; margin: 8px 0 0; font-size: 13px; }
            .summary { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin: 22px 0; }
            .box { border: 1px solid #d1d5db; border-radius: 8px; padding: 14px; background: #f9fafb; }
            .label { color: #6b7280; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; margin: 0; }
            .value { font-size: 22px; font-weight: 800; margin: 6px 0 0; }
            table { border-collapse: collapse; width: 100%; margin-top: 18px; font-size: 13px; }
            th, td { border: 1px solid #d1d5db; padding: 9px; text-align: left; }
            th { background: #0f766e; color: white; }
            tr:nth-child(even) td { background: #f9fafb; }
            span { color: #6b7280; font-size: 11px; }
            .footer { margin-top: 24px; color: #6b7280; font-size: 12px; border-top: 1px solid #d1d5db; padding-top: 12px; }
          </style>
        </head>
        <body>
          <div class="header">
            <h1 class="brand">Netrue Smart Incubator</h1>
            <p class="title">Daily Power Consumption Report</p>
            <p class="meta">GMT day: ${gmtDayLabel(data.rtc_time)} | Period: 12:00 AM - 11:59 PM GMT | Printed: ${new Date(data.rtc_time).toUTCString()}</p>
          </div>
          <div class="summary">
            <div class="box"><p class="label">Total Power Used Today</p><p class="value">${wh(data.energy_today_wh)}</p></div>
            <div class="box"><p class="label">Last Completed Hour (${data.last_completed_hour_label})</p><p class="value">${wh(data.energy_last_hour_wh)}</p></div>
            <div class="box"><p class="label">Current Hour So Far (${data.current_hour_label})</p><p class="value">${wh(data.energy_current_hour_wh)}</p></div>
          </div>
          <table>
            <thead><tr><th>Hour</th><th>Power Consumption</th></tr></thead>
            <tbody>${body}</tbody>
          </table>
          <div class="footer">Generated by Netrue Smart Incubator Power Management. Completed GMT hours are final; only the current hour row changes until the hour closes.</div>
        </body>
      </html>
    `);
    win.document.close();
    win.print();
  };

  return (
    <form className="space-y-6" onSubmit={save}>
      <div className={backupEnabled ? "grid gap-5 lg:grid-cols-[1fr_360px]" : "grid gap-5"}>
        <Card className="overflow-hidden border-primary/20 bg-[linear-gradient(135deg,rgba(20,184,166,0.16),rgba(255,255,255,0.72))] dark:bg-[linear-gradient(135deg,rgba(20,184,166,0.20),rgba(17,24,39,0.72))]">
          <CardContent className="p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium uppercase tracking-wide text-primary">Power Consumed Today</p>
                <h1 className="mt-3 text-5xl font-bold">{wh(data.energy_today_wh)}</h1>
                <p className="mt-3 text-sm text-foreground/65">Last hour power consumption ({data.last_completed_hour_label}): {wh(data.energy_last_hour_wh)}</p>
                <p className="mt-1 text-sm text-foreground/55">Current hour so far ({data.current_hour_label}): {wh(data.energy_current_hour_wh)}</p>
              </div>
              <div className="rounded-md bg-primary/10 p-3 text-primary">
                <BoltIcon className="h-8 w-8" />
              </div>
            </div>
          </CardContent>
        </Card>

        {backupEnabled ? (
          <Card className="border-accent/40 bg-card">
            <CardContent className="p-6">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-medium uppercase tracking-wide text-accent">Usable Battery Energy Left</p>
                  <h2 className="mt-3 text-4xl font-bold">{wh(data.battery.energy_wh)}</h2>
                </div>
                <div className="rounded-md bg-accent/10 p-3 text-accent">
                  <Battery100Icon className="h-7 w-7" />
                </div>
              </div>
              <p className="mt-4 text-sm text-foreground/65">
                Uses {data.config.battery_usable_percent}% battery depth and {data.config.inverter_efficiency_percent}% inverter efficiency.
              </p>
              <p className="mt-2 text-sm text-foreground/65">Estimated time left: {runtime(data.battery.runtime_hours)}</p>
              <p className="mt-2 text-sm text-foreground/65">Recharge before: {data.recharge_before ? new Date(data.recharge_before).toLocaleString() : "--"}</p>
            </CardContent>
          </Card>
        ) : null}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Hourly Power Consumption - GMT Day</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-6 lg:grid-cols-[1fr_360px]">
          <div className="h-72">
            <Bar data={chartData} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { title: { display: true, text: "Wh" } } } }} />
          </div>
          <div className="max-h-72 overflow-auto rounded-md border border-border">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-muted text-left">
                <tr>
                  <th className="px-3 py-2">Hour</th>
                  <th className="px-3 py-2">Used</th>
                </tr>
              </thead>
              <tbody>
                {printedRows.map((row) => (
                  <tr key={row.created_at} className="border-t border-border">
                    <td className="px-3 py-2">
                      {row.hour}
                      {row.hour === data.current_hour_label.slice(0, 5) ? <span className="ml-2 text-xs text-foreground/50">current</span> : null}
                    </td>
                    <td className="px-3 py-2 font-medium">{wh(row.energy_wh)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Power Setup</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <label className="flex items-center gap-3 text-sm xl:col-span-4">
            <input type="checkbox" checked={form.battery_backup_enabled} onChange={(event) => setForm({ ...form, battery_backup_enabled: event.target.checked })} />
            Enable backup battery runtime card
          </label>
          <label className="space-y-2 text-sm">Battery voltage<Input type="number" step="0.1" value={form.battery_voltage} onChange={(event) => setForm({ ...form, battery_voltage: Number(event.target.value) })} /></label>
          <label className="space-y-2 text-sm">Battery capacity Ah<Input type="number" step="0.1" value={form.battery_capacity_ah} onChange={(event) => setForm({ ...form, battery_capacity_ah: Number(event.target.value) })} /></label>
          <label className="space-y-2 text-sm">Usable battery %<Input type="number" step="1" value={form.battery_usable_percent} onChange={(event) => setForm({ ...form, battery_usable_percent: Number(event.target.value) })} /></label>
          <label className="space-y-2 text-sm">Inverter efficiency %<Input type="number" step="1" value={form.inverter_efficiency_percent} onChange={(event) => setForm({ ...form, inverter_efficiency_percent: Number(event.target.value) })} /></label>
          <label className="space-y-2 text-sm">Battery charge %<Input type="number" step="1" value={form.battery_charge_percent} onChange={(event) => setForm({ ...form, battery_charge_percent: Number(event.target.value) })} /></label>
          <label className="space-y-2 text-sm">Battery health %<Input type="number" step="1" value={form.battery_health_percent} onChange={(event) => setForm({ ...form, battery_health_percent: Number(event.target.value) })} /></label>
          <label className="space-y-2 text-sm">Battery type<Select value={form.battery_chemistry} onChange={(event) => setForm({ ...form, battery_chemistry: event.target.value })}><option>Gel</option><option>Lead Acid</option><option>AGM</option><option>LiFePO4</option><option>Lithium Ion</option></Select></label>
          <label className="space-y-2 text-sm">Heater watts<Input type="number" step="0.1" value={form.heater_watts} onChange={(event) => setForm({ ...form, heater_watts: Number(event.target.value) })} /></label>
        </CardContent>
      </Card>

      <div className="flex flex-wrap gap-3">
        <Button type="submit">Save Power Setup</Button>
        <Button type="button" className="bg-muted text-foreground" onClick={printReport}><DocumentArrowDownIcon className="h-5 w-5" /> Download PDF</Button>
        <Button type="button" className="bg-muted text-foreground" onClick={printReport}><PrinterIcon className="h-5 w-5" /> Print Report</Button>
        <Button type="button" className="bg-muted text-foreground" onClick={csv}><ArrowDownTrayIcon className="h-5 w-5" /> Download CSV</Button>
      </div>
    </form>
  );
}
