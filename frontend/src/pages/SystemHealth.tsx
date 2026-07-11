import { Activity, CheckCircle2, CircleAlert, CirclePause, Siren } from "lucide-react";
import { useEffect, useState } from "react";
import { incubatorApi } from "../api/client";
import { StatusCard } from "../components/StatusCard";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Skeleton } from "../components/ui/skeleton";
import { cn, formatTime } from "../lib/utils";
import type { SystemHealth as SystemHealthPayload } from "../types/incubator";

const icons = {
  ok: CheckCircle2,
  warning: CircleAlert,
  critical: Siren,
  idle: CirclePause
};

export function SystemHealth() {
  const [data, setData] = useState<SystemHealthPayload | null>(null);

  useEffect(() => {
    incubatorApi.systemHealth().then(setData).catch(console.error);
  }, []);

  if (!data) return <Skeleton className="h-[70vh] w-full" />;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        <StatusCard label="System State" value={data.state.toUpperCase()} icon={<Activity />} />
        <StatusCard label="Health Score" value={`${data.score}%`} />
        <StatusCard label="Open Alerts" value={data.unacknowledged_alerts} />
        <StatusCard label="Queue Size" value={data.queue_size} />
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Hardware Health Monitor</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2">
          {data.modules.map((module) => {
            const Icon = icons[module.state];
            return (
              <div key={module.module} className="flex min-h-20 items-center gap-3 rounded-md border border-border p-4">
                <div
                  className={cn(
                    "rounded-md p-2",
                    module.state === "ok" && "bg-emerald-500/10 text-emerald-600",
                    module.state === "warning" && "bg-amber-500/10 text-amber-600",
                    module.state === "critical" && "bg-destructive/10 text-destructive",
                    module.state === "idle" && "bg-muted text-foreground/60"
                  )}
                >
                  <Icon size={20} />
                </div>
                <div>
                  <p className="font-semibold capitalize">{module.module.replace("-", " ")}</p>
                  <p className="text-sm text-foreground/60">{module.detail}</p>
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>
      <p className="text-sm text-foreground/60">Last checked: {formatTime(data.checked_at)}</p>
    </div>
  );
}
