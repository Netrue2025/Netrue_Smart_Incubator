import { Download, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input, Select } from "../components/ui/input";
import { downloadFile, formatTime } from "../lib/utils";
import { useIncubatorStore } from "../store/incubator";

export function History() {
  const { history, loadHistory } = useIncubatorStore();
  const [range, setRange] = useState("today");
  const [query, setQuery] = useState("");
  useEffect(() => {
    loadHistory(range).catch(console.error);
  }, [range, loadHistory]);
  const rows = useMemo(
    () => history.readings.filter((r) => `${r.temperature} ${r.humidity} ${r.relay} ${r.fan_relay}`.toLowerCase().includes(query.toLowerCase())),
    [history.readings, query]
  );
  const csv = () => ["time,temperature,humidity,heat_index,relay,fan_relay", ...rows.map((r) => `${r.created_at},${r.temperature},${r.humidity},${r.heat_index},${r.relay},${r.fan_relay}`)].join("\n");
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-3">
        <Select className="max-w-44" value={range} onChange={(e) => setRange(e.target.value)}>
          <option value="today">Today</option>
          <option value="week">Week</option>
          <option value="month">Month</option>
        </Select>
        <div className="relative max-w-sm flex-1">
          <Search className="absolute left-3 top-2.5 text-foreground/50" size={18} />
          <Input className="pl-10" placeholder="Search readings" value={query} onChange={(e) => setQuery(e.target.value)} />
        </div>
        <Button onClick={() => downloadFile("history.csv", csv(), "text/csv")}>
          <Download size={18} /> CSV
        </Button>
        <Button onClick={() => downloadFile("history.json", JSON.stringify(rows, null, 2), "application/json")}>JSON</Button>
        <Button onClick={() => downloadFile("history.xls", csv(), "application/vnd.ms-excel")}>Excel</Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Sensor Logs</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="border-b border-border text-foreground/60">
              <tr>
                <th className="py-3">Time</th>
                <th>Temperature</th>
                <th>Humidity</th>
                <th>Heat Index</th>
                <th>Relay</th>
                <th>Fan</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={`${row.created_at}-${index}`} className="border-b border-border/70">
                  <td className="py-3">{formatTime(row.created_at)}</td>
                  <td>{row.temperature.toFixed(1)} C</td>
                  <td>{row.humidity.toFixed(1)}%</td>
                  <td>{row.heat_index.toFixed(1)} C</td>
                  <td>{row.relay ? "ON" : "OFF"}</td>
                  <td>{row.fan_relay ? "ON" : "OFF"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
