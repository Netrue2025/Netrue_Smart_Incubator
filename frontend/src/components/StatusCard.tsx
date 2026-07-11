import type { ReactNode } from "react";
import { Card, CardContent } from "./ui/card";

export function StatusCard({ label, value, icon }: { label: string; value: ReactNode; icon?: ReactNode }) {
  return (
    <Card>
      <CardContent className="flex min-h-24 items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-foreground/60">{label}</p>
          <div className="mt-2 text-xl font-semibold">{value}</div>
        </div>
        {icon && <div className="rounded-md bg-muted p-3 text-primary">{icon}</div>}
      </CardContent>
    </Card>
  );
}
