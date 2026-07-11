import { RotateCw, Timer, TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { incubatorApi } from "../api/client";
import { StatusCard } from "../components/StatusCard";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Skeleton } from "../components/ui/skeleton";
import { formatTime } from "../lib/utils";
import type { ServoAnalytics as ServoAnalyticsPayload } from "../types/incubator";

export function ServoAnalytics() {
  const [data, setData] = useState<ServoAnalyticsPayload | null>(null);
  const [history, setHistory] = useState<unknown[]>([]);

  useEffect(() => {
    Promise.all([incubatorApi.servo(), incubatorApi.analyticsHistory("servo", 20)])
      .then(([servo, rows]) => {
        setData(servo);
        setHistory(rows.items);
      })
      .catch(console.error);
  }, []);

  if (!data) return <Skeleton className="h-[70vh] w-full" />;

  const completion = data.expected_cycles_per_day ? Math.min(100, Math.round((data.completed_today / data.expected_cycles_per_day) * 100)) : 0;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        <StatusCard label="Tray Turning" value={data.enabled ? "Enabled" : "Disabled"} icon={<RotateCw />} />
        <StatusCard label="Target Angle" value={`${data.target_angle} deg`} />
        <StatusCard label="Interval" value={`${data.interval_minutes} min`} icon={<Timer />} />
        <StatusCard label="Failures Today" value={data.failures_today} icon={<TriangleAlert />} />
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Servo Cycle Progress</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="h-3 overflow-hidden rounded-full bg-muted">
            <div className="h-full bg-primary" style={{ width: `${completion}%` }} />
          </div>
          <div className="grid gap-3 text-sm sm:grid-cols-3">
            <p><span className="text-foreground/60">Completed today:</span> {data.completed_today}</p>
            <p><span className="text-foreground/60">Expected cycles:</span> {data.expected_cycles_per_day}</p>
            <p><span className="text-foreground/60">Profile turning:</span> {data.profile_turning_enabled ? "Allowed" : "Paused"}</p>
          </div>
          <p className="text-sm text-foreground/60">
            Last event: {data.last_event ? `${data.last_event.event_type} at ${formatTime(data.last_event.created_at)}` : "Waiting for servo events"}
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Servo History</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full min-w-[620px] text-left text-sm">
            <thead className="text-xs uppercase text-foreground/60">
              <tr><th className="py-2">Time</th><th>Event</th><th>Angle</th><th>Duration</th><th>Status</th><th>Message</th></tr>
            </thead>
            <tbody>
              {history.map((row) => {
                const item = row as { id: number; created_at: string; event_type: string; target_angle: number; duration_seconds: number; success: boolean; message: string };
                return (
                  <tr key={item.id} className="border-t border-border">
                    <td className="py-2">{formatTime(item.created_at)}</td>
                    <td>{item.event_type}</td>
                    <td>{item.target_angle} deg</td>
                    <td>{item.duration_seconds}s</td>
                    <td>{item.success ? "OK" : "Failed"}</td>
                    <td>{item.message || "--"}</td>
                  </tr>
                );
              })}
              {!history.length && <tr><td className="py-4 text-foreground/60" colSpan={6}>No servo history has been posted yet.</td></tr>}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
