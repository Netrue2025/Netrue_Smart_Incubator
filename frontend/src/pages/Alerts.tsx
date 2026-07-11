import { CheckCircle2 } from "lucide-react";
import { useEffect } from "react";
import { incubatorApi } from "../api/client";
import { useToast } from "../components/Toast";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { formatTime } from "../lib/utils";
import { useIncubatorStore } from "../store/incubator";

export function Alerts() {
  const { alerts, loadAlerts } = useIncubatorStore();
  const toast = useToast();
  useEffect(() => {
    loadAlerts().catch(console.error);
  }, [loadAlerts]);
  const ack = async (id: number) => {
    await incubatorApi.ackAlert(id);
    toast("Alert acknowledged");
    await loadAlerts();
  };
  return (
    <Card>
      <CardHeader>
        <CardTitle>Alerts</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {alerts.map((alert) => (
          <div key={alert.id} className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-border p-4">
            <div>
              <p className="font-semibold capitalize">{alert.type.replaceAll("_", " ")}</p>
              <p className="text-sm text-foreground/70">{alert.message}</p>
              <p className="text-xs text-foreground/50">{formatTime(alert.created_at)} · {alert.severity}</p>
            </div>
            {!alert.acknowledged && (
              <Button onClick={() => ack(alert.id)}>
                <CheckCircle2 size={18} /> Acknowledge
              </Button>
            )}
          </div>
        ))}
        {alerts.length === 0 && <p className="text-sm text-foreground/60">No alerts recorded.</p>}
      </CardContent>
    </Card>
  );
}
