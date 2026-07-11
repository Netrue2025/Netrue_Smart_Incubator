import { BatteryCharging, CalendarDays, Cloud, Database, Fan, Flame, RotateCw, Server, ShieldCheck, Thermometer, Wifi } from "lucide-react";
import { useEffect, useState } from "react";
import { incubatorApi } from "../api/client";
import { Gauge } from "../components/Gauge";
import { LiveChart } from "../components/LiveChart";
import { StatusCard } from "../components/StatusCard";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Skeleton } from "../components/ui/skeleton";
import { formatTime } from "../lib/utils";
import { useIncubatorStore } from "../store/incubator";
import type { HeaterAnalytics, IncubationPayload, PowerSummary, ServoAnalytics, SystemHealth } from "../types/incubator";

export function Overview() {
  const { status, history, loadStatus } = useIncubatorStore();
  const [incubation, setIncubation] = useState<IncubationPayload | null>(null);
  const [servo, setServo] = useState<ServoAnalytics | null>(null);
  const [heater, setHeater] = useState<HeaterAnalytics | null>(null);
  const [power, setPower] = useState<PowerSummary | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  useEffect(() => {
    loadStatus().catch(console.error);
    const refresh = window.setInterval(() => loadStatus().catch(console.error), 5000);
    Promise.all([incubatorApi.incubation(), incubatorApi.servo(), incubatorApi.heater(), incubatorApi.power(), incubatorApi.systemHealth()])
      .then(([incubationPayload, servoPayload, heaterPayload, powerPayload, healthPayload]) => {
        setIncubation(incubationPayload);
        setServo(servoPayload);
        setHeater(heaterPayload);
        setPower(powerPayload);
        setHealth(healthPayload);
      })
      .catch(console.error);
    return () => window.clearInterval(refresh);
  }, [loadStatus]);

  if (!status) {
    return <Skeleton className="h-[70vh] w-full" />;
  }
  const reading = status.environment;
  const settings = status.settings;
  const hasReading = Boolean(reading);
  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-[1fr_380px]">
        <Card>
          <CardContent className="grid min-h-[360px] items-center gap-6 py-8 md:grid-cols-2">
            {hasReading ? (
              <>
                <Gauge label="Temperature" value={reading?.temperature ?? 0} min={20} max={45} unit=" C" target={settings.target_temperature} large />
                <Gauge label="Humidity" value={reading?.humidity ?? 0} min={20} max={95} unit="%" target={settings.target_humidity} large />
              </>
            ) : (
              <div className="flex min-h-64 flex-col items-center justify-center text-center md:col-span-2">
                <p className="text-2xl font-semibold">Waiting for ESP32 data</p>
                <p className="mt-2 max-w-md text-sm text-foreground/60">
                  No fresh incubator reading has reached the backend yet. Flash the ESP32 and check Serial Monitor for HTTP 200 posts.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-1">
          <StatusCard label="Relay Status" value={reading ? (reading.relay ? "ON" : "OFF") : "Waiting"} icon={<Flame />} />
          <StatusCard label="Fan Relay" value={reading ? (reading.fan_relay ? "ON" : "OFF") : "Waiting"} icon={<Fan />} />
          <StatusCard label="Heating" value={settings.relay_mode} icon={<Thermometer />} />
          <StatusCard label="WiFi" value={status.device.wifi ? "Connected" : "Offline"} icon={<Wifi />} />
          <StatusCard label="Cloud Sync" value={status.device.sync_status} icon={<Cloud />} />
        </div>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatusCard label="Latest Temperature" value={reading ? `${reading.temperature.toFixed(1)} C` : "--"} />
        <StatusCard label="Latest Humidity" value={reading ? `${reading.humidity.toFixed(1)}%` : "--"} />
        <StatusCard label="ESP32 Online" value={status.device.online ? "Online" : "Waiting"} />
        <StatusCard label="Backend Online" value={status.backend.online ? "Online" : "Offline"} icon={<Server />} />
        <StatusCard label="Database" value={status.backend.database} icon={<Database />} />
        <StatusCard label="Current Time" value={formatTime(status.time)} />
        <StatusCard label="Last Sync" value={formatTime(status.device.last_sync)} />
        <StatusCard label="Data Refresh" value="On page load" />
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <StatusCard label="Incubation Day" value={incubation?.active ? `Day ${incubation.active.current_day}` : "Not set"} icon={<CalendarDays />} />
        <StatusCard label="Hatch Countdown" value={incubation?.active ? `${incubation.active.days_remaining} days` : "--"} />
        <StatusCard label="Servo Cycles" value={servo ? `${servo.completed_today}/${servo.expected_cycles_per_day}` : "--"} icon={<RotateCw />} />
        <StatusCard label="Heater Cycles" value={heater ? heater.cycles : "--"} icon={<Flame />} />
        <StatusCard label="Energy 24h" value={power ? `${power.total_kwh} kWh` : "--"} icon={<BatteryCharging />} />
        <StatusCard label="System Health" value={health ? `${health.score}%` : "--"} icon={<ShieldCheck />} />
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Live Environment</CardTitle>
        </CardHeader>
        <CardContent>
          <LiveChart readings={history.readings} type="environment" />
        </CardContent>
      </Card>
    </div>
  );
}
