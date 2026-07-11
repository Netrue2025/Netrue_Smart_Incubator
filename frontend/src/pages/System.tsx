import { useEffect, useState } from "react";
import { incubatorApi } from "../api/client";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { formatTime } from "../lib/utils";

export function System() {
  const [system, setSystem] = useState<Record<string, unknown>>({});
  useEffect(() => {
    incubatorApi.system().then(setSystem).catch(console.error);
  }, []);
  return (
    <Card>
      <CardHeader>
        <CardTitle>System</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {Object.entries(system).map(([key, value]) => (
          <div key={key} className="rounded-md border border-border p-4">
            <p className="text-xs uppercase tracking-wide text-foreground/60">{key.replaceAll("_", " ")}</p>
            <p className="mt-2 font-semibold">{typeof value === "string" && value.includes("T") ? formatTime(value) : String(value ?? "Pending device report")}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
