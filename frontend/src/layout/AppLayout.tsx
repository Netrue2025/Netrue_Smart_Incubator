import { Activity, AlertTriangle, BatteryCharging, CalendarDays, Flame, Gauge, History, Home, Info, Moon, RotateCw, Settings, ShieldCheck, SlidersHorizontal, Sun, Thermometer } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { useEffect, useState } from "react";
import { cn } from "../lib/utils";
import { useIncubatorStore } from "../store/incubator";

const nav = [
  { to: "/", label: "Overview", icon: Home },
  { to: "/incubation", label: "Incubation", icon: CalendarDays },
  { to: "/environment", label: "Environment", icon: Thermometer },
  { to: "/control", label: "Control", icon: SlidersHorizontal },
  { to: "/servo", label: "Servo", icon: RotateCw },
  { to: "/heater", label: "Heater", icon: Flame },
  { to: "/power", label: "Power", icon: BatteryCharging },
  { to: "/system-health", label: "Health", icon: ShieldCheck },
  { to: "/history", label: "History", icon: History },
  { to: "/alerts", label: "Alerts", icon: AlertTriangle },
  { to: "/settings", label: "Settings", icon: Settings },
  { to: "/system", label: "System", icon: Activity },
  { to: "/about", label: "About", icon: Info }
];

export function AppLayout() {
  const [dark, setDark] = useState(() => localStorage.theme === "dark");
  const connectLive = useIncubatorStore((state) => state.connectLive);
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.theme = dark ? "dark" : "light";
  }, [dark]);
  useEffect(() => connectLive(), [connectLive]);
  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r border-border bg-card lg:block">
        <div className="flex h-16 items-center gap-3 border-b border-border px-5">
          <Gauge className="text-primary" />
          <div>
            <p className="text-sm font-bold">Smart AI Incubator</p>
            <p className="text-xs text-foreground/60">V2 Control Room</p>
          </div>
        </div>
        <nav className="space-y-1 p-3">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn("flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-foreground/70 transition hover:bg-muted", isActive && "bg-muted text-foreground")
              }
            >
              <item.icon size={18} />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="lg:pl-64">
        <header className="sticky top-0 z-20 flex min-h-16 items-center justify-between border-b border-border bg-background/90 px-4 backdrop-blur md:px-8">
          <div>
            <h1 className="text-lg font-semibold">Incubator Operations</h1>
            <p className="text-xs text-foreground/60">Offline-first environmental monitoring and control</p>
          </div>
          <button title="Toggle dark mode" className="rounded-md border border-border p-2" onClick={() => setDark((value) => !value)}>
            {dark ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </header>
        <div className="border-b border-border bg-card lg:hidden">
          <nav className="flex gap-1 overflow-x-auto px-3 py-2">
            {nav.map((item) => (
              <NavLink key={item.to} to={item.to} className={({ isActive }) => cn("flex min-w-fit items-center gap-2 rounded-md px-3 py-2 text-xs", isActive && "bg-muted")}>
                <item.icon size={16} />
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
        <section className="p-4 md:p-8">
          <Outlet />
        </section>
      </main>
    </div>
  );
}
