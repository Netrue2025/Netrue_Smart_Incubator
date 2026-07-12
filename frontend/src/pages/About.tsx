import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";

export function About() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Smart AI Incubator V2</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 text-sm leading-6 text-foreground/75">
        <p>
          This dashboard manages an offline-first ESP32 incubator with local relay safety, DHT22 telemetry,
          MySQL history, queued commands, and live HTTP polling.
        </p>
        <p>
          The firmware keeps reading sensors and controlling heat without WiFi. The backend stores telemetry,
          validates settings, raises alerts, and queues commands until the device reconnects.
        </p>
      </CardContent>
    </Card>
  );
}
