import { CheckCircle2, RotateCw, Timer, TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { incubatorApi } from "../api/client";
import { StatusCard } from "../components/StatusCard";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Skeleton } from "../components/ui/skeleton";
import { formatTime } from "../lib/utils";
import type { ServoAnalytics as ServoAnalyticsPayload } from "../types/incubator";

type ServoHistoryRow = NonNullable<ServoAnalyticsPayload["last_event"]>;

export function ServoAnalytics() {
  const [data, setData] = useState<ServoAnalyticsPayload | null>(null);
  const [history, setHistory] = useState<ServoHistoryRow[]>([]);
  const [nowMs, setNowMs] = useState(Date.now());

  useEffect(() => {
    Promise.all([incubatorApi.servo(), incubatorApi.analyticsHistory("servo", 20)])
      .then(([servo, rows]) => {
        setData(servo);
        setHistory(rows.items as ServoHistoryRow[]);
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => setNowMs(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  if (!data) return <Skeleton className="h-[70vh] w-full" />;

  const completion = data.expected_cycles_per_day ? Math.min(100, Math.round((data.completed_today / data.expected_cycles_per_day) * 100)) : 0;
  const failureNote = data.failure_reasons.length
    ? data.failure_reasons.map((item) => `${formatTime(item.created_at)}: ${item.message}`).join("\n")
    : "No failed turns recorded today";
  const nextTurnMs = data.next_turn_at ? new Date(data.next_turn_at).getTime() : null;
  const countdownSeconds = nextTurnMs ? Math.max(0, Math.ceil((nextTurnMs - nowMs) / 1000)) : null;
  const countdownLabel =
    countdownSeconds === null
      ? "--"
      : countdownSeconds <= 0
        ? "Due now"
        : `${Math.floor(countdownSeconds / 3600)}h ${Math.floor((countdownSeconds % 3600) / 60)}m ${countdownSeconds % 60}s`;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-5">
        <StatusCard label="Tray Turning" value={data.enabled ? "Enabled" : "Disabled"} icon={<RotateCw />} />
        <StatusCard label="Target Angle" value={`${data.target_angle} deg`} />
        <StatusCard label="Interval" value={`${data.interval_minutes} min`} icon={<Timer />} />
        <StatusCard label="Next Move" value={countdownLabel} icon={<Timer />} />
        <Card title={failureNote}>
          <CardContent className="flex min-h-24 items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-wide text-foreground/60">Failures Today</p>
              <div className="mt-2 text-xl font-semibold">{data.failures_today}</div>
            </div>
            <div className="rounded-md bg-muted p-3 text-primary"><TriangleAlert /></div>
          </CardContent>
        </Card>
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
          <div className="grid gap-3 text-sm sm:grid-cols-3">
            <p><span className="text-foreground/60">Next target:</span> {data.next_target_angle === null ? "--" : `${data.next_target_angle > 0 ? "+" : ""}${data.next_target_angle} deg`}</p>
            <p><span className="text-foreground/60">Next time:</span> {data.next_turn_at ? formatTime(data.next_turn_at) : "--"}</p>
            <p><span className="text-foreground/60">Countdown:</span> {countdownLabel}</p>
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
              {history.map((item) => (
                <tr key={item.id} className="border-t border-border">
                  <td className="py-2">{formatTime(item.created_at)}</td>
                  <td>{item.event_type}</td>
                  <td>{item.target_angle} deg</td>
                  <td>{Number(item.duration_seconds).toFixed(1)}s</td>
                  <td>
                    <span className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-semibold ${item.success ? "bg-primary/10 text-primary" : "bg-red-500/10 text-red-600"}`}>
                      {item.success ? <CheckCircle2 className="h-3.5 w-3.5" /> : <TriangleAlert className="h-3.5 w-3.5" />}
                      {item.success ? "OK" : "Failed"}
                    </span>
                  </td>
                  <td title={item.message || ""}>{item.message || "--"}</td>
                </tr>
              ))}
              {!history.length && <tr><td className="py-4 text-foreground/60" colSpan={6}>No servo history has been posted yet.</td></tr>}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
