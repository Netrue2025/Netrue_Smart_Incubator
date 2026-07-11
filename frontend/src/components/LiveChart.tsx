import { Area, AreaChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Reading } from "../types/incubator";

export function LiveChart({ readings, type }: { readings: Reading[]; type: "environment" | "relay" }) {
  const data = readings.map((reading) => ({
    time: new Date(reading.created_at || reading.timestamp || Date.now()).toLocaleTimeString(),
    temperature: reading.temperature,
    humidity: reading.humidity,
    relay: reading.relay ? 1 : 0
  }));
  if (type === "relay") {
    return (
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.25} />
          <XAxis dataKey="time" minTickGap={30} />
          <YAxis domain={[0, 1]} />
          <Tooltip />
          <Line type="stepAfter" dataKey="relay" stroke="hsl(var(--accent))" dot={false} strokeWidth={3} />
        </LineChart>
      </ResponsiveContainer>
    );
  }
  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" opacity={0.25} />
        <XAxis dataKey="time" minTickGap={30} />
        <YAxis />
        <Tooltip />
        <Area type="monotone" dataKey="temperature" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={0.18} strokeWidth={3} />
        <Area type="monotone" dataKey="humidity" stroke="hsl(var(--accent))" fill="hsl(var(--accent))" fillOpacity={0.14} strokeWidth={3} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
