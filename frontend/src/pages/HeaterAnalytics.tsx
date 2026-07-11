import { Flame, Gauge, Timer } from "lucide-react";
import { useEffect, useState } from "react";
import { incubatorApi } from "../api/client";
import { StatusCard } from "../components/StatusCard";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Skeleton } from "../components/ui/skeleton";
import { formatTime } from "../lib/utils";
import type { HeaterAnalytics as HeaterAnalyticsPayload } from "../types/incubator";

export function HeaterAnalytics() {
  const [data, setData] = useState<HeaterAnalyticsPayload | null>(null);

  useEffect(() => {
    incubatorApi.heater().then(setData).catch(console.error);
  }, []);

  if (!data) return <Skeleton className="h-[70vh] w-full" />;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        <StatusCard label="Heater State" value={data.currently_on ? "ON" : "OFF"} icon={<Flame />} />
        <StatusCard label="Cycles 24h" value={data.cycles} icon={<Gauge />} />
        <StatusCard label="Runtime 24h" value={`${data.runtime_minutes} min`} icon={<Timer />} />
        <StatusCard label="Duty Cycle" value={`${data.duty_cycle_percent}%`} />
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Temperature Stability</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-3">
          <StatusCard label="Average" value={data.average_temperature === null ? "--" : `${data.average_temperature.toFixed(1)} C`} />
          <StatusCard label="Minimum" value={data.min_temperature === null ? "--" : `${data.min_temperature.toFixed(1)} C`} />
          <StatusCard label="Maximum" value={data.max_temperature === null ? "--" : `${data.max_temperature.toFixed(1)} C`} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Recent Relay Events</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-left text-sm">
            <thead className="text-xs uppercase text-foreground/60">
              <tr><th className="py-2">Time</th><th>Relay</th><th>Mode</th><th>Reason</th></tr>
            </thead>
            <tbody>
              {data.recent_events.map((event) => (
                <tr key={event.id} className="border-t border-border">
                  <td className="py-2">{formatTime(event.created_at)}</td>
                  <td>{event.relay ? "ON" : "OFF"}</td>
                  <td>{event.mode}</td>
                  <td>{event.reason}</td>
                </tr>
              ))}
              {!data.recent_events.length && <tr><td className="py-4 text-foreground/60" colSpan={4}>No relay events in the last 24 hours.</td></tr>}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
