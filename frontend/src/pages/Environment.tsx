import { Download } from "lucide-react";
import { useEffect } from "react";
import { LiveChart } from "../components/LiveChart";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { downloadFile } from "../lib/utils";
import { useIncubatorStore } from "../store/incubator";

export function Environment() {
  const { history, loadHistory } = useIncubatorStore();
  useEffect(() => {
    loadHistory("today").catch(console.error);
  }, [loadHistory]);
  const exportCsv = () => {
    const lines = ["time,temperature,humidity,heat_index,relay,fan_relay"];
    history.readings.forEach((r) => lines.push(`${r.created_at},${r.temperature},${r.humidity},${r.heat_index},${r.relay},${r.fan_relay}`));
    downloadFile("environment.csv", lines.join("\n"), "text/csv");
  };
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold">Environment</h2>
          <p className="text-sm text-foreground/60">Temperature, humidity, heat index, and relay trend.</p>
        </div>
        <Button onClick={exportCsv}>
          <Download size={18} /> Export CSV
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Temperature and Humidity</CardTitle>
        </CardHeader>
        <CardContent>
          <LiveChart readings={history.readings} type="environment" />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Relay Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <LiveChart readings={history.readings} type="relay" />
        </CardContent>
      </Card>
    </div>
  );
}
