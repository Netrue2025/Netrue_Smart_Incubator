import { CalendarDays, Save } from "lucide-react";
import type { CSSProperties, FormEvent } from "react";
import { useEffect, useState } from "react";
import { incubatorApi } from "../api/client";
import { useToast } from "../components/Toast";
import { StatusCard } from "../components/StatusCard";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input, Select } from "../components/ui/input";
import { Skeleton } from "../components/ui/skeleton";

type ProfileForm = {
  bird_category: string;
  custom_bird: string;
  batch_name: string;
  egg_count: number;
  loading_date: string;
  incubation_days: number;
  lockdown_day: number;
  target_temperature: number;
  target_humidity: number;
  turning_enabled: boolean;
  turning_disabled_day: number;
  notes: string;
  is_active: boolean;
};

type ActiveIncubation = NonNullable<Awaited<ReturnType<typeof incubatorApi.incubation>>["active"]>;

const defaults: Record<string, Pick<ProfileForm, "incubation_days" | "lockdown_day" | "turning_disabled_day" | "target_temperature" | "target_humidity">> = {
  chicken: { incubation_days: 21, lockdown_day: 18, turning_disabled_day: 18, target_temperature: 37.5, target_humidity: 60 },
  duck: { incubation_days: 28, lockdown_day: 25, turning_disabled_day: 25, target_temperature: 37.5, target_humidity: 65 },
  quail: { incubation_days: 17, lockdown_day: 14, turning_disabled_day: 14, target_temperature: 37.5, target_humidity: 58 },
  turkey: { incubation_days: 28, lockdown_day: 25, turning_disabled_day: 25, target_temperature: 37.5, target_humidity: 60 },
  goose: { incubation_days: 30, lockdown_day: 27, turning_disabled_day: 27, target_temperature: 37.4, target_humidity: 65 },
  custom: { incubation_days: 21, lockdown_day: 18, turning_disabled_day: 18, target_temperature: 37.5, target_humidity: 60 }
};

function today() {
  return new Date().toISOString().slice(0, 10);
}

function emptyForm(): ProfileForm {
  return {
    bird_category: "chicken",
    custom_bird: "",
    batch_name: "Main batch",
    egg_count: 0,
    loading_date: today(),
    ...defaults.chicken,
    turning_enabled: true,
    notes: "",
    is_active: true
  };
}

function embryoStage(active: ActiveIncubation) {
  const progress = active.current_day / Math.max(1, active.incubation_days);
  if (progress < 0.18) return { name: "Early cells", detail: "Warmth is building the first visible form.", scale: 0.7, veins: 3 };
  if (progress < 0.34) return { name: "Heart and head", detail: "A tiny heartbeat stage with early body shape.", scale: 0.84, veins: 5 };
  if (progress < 0.52) return { name: "Body forming", detail: "Limb buds and the curved body are taking shape.", scale: 0.98, veins: 7 };
  if (progress < 0.72) return { name: "Feather lines", detail: "The embryo is larger, with stronger movement.", scale: 1.12, veins: 9 };
  if (progress < 0.9) return { name: "Lockdown prep", detail: "The chick fills more of the egg and stores strength.", scale: 1.24, veins: 11 };
  return { name: "Hatch watch", detail: "The final position is forming for hatch day.", scale: 1.32, veins: 12 };
}

function EmbryoDayVisual({ active }: { active: ActiveIncubation }) {
  const stage = embryoStage(active);
  const progress = Math.min(100, Math.max(0, active.progress_percent));
  const shellCracks = active.current_day >= active.lockdown_day;
  const veinAngles = Array.from({ length: stage.veins }, (_, index) => -58 + index * (116 / Math.max(1, stage.veins - 1)));

  return (
    <div className="embryo-visual" aria-label={`Day ${active.current_day} embryo stage`}>
      <svg viewBox="0 0 260 320" role="img">
        <defs>
          <radialGradient id="eggGlow" cx="45%" cy="32%" r="72%">
            <stop offset="0%" stopColor="#fff8df" />
            <stop offset="54%" stopColor="#f7d98c" />
            <stop offset="100%" stopColor="#d9883d" />
          </radialGradient>
          <radialGradient id="embryoGlow" cx="42%" cy="34%" r="70%">
            <stop offset="0%" stopColor="#fbd0b9" />
            <stop offset="58%" stopColor="#e76f51" />
            <stop offset="100%" stopColor="#9f2d2d" />
          </radialGradient>
          <linearGradient id="shellShine" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0%" stopColor="rgba(255,255,255,0.92)" />
            <stop offset="100%" stopColor="rgba(255,255,255,0.08)" />
          </linearGradient>
        </defs>
        <ellipse cx="130" cy="164" rx="98" ry="132" fill="url(#eggGlow)" opacity="0.95" />
        <ellipse cx="104" cy="104" rx="34" ry="66" fill="url(#shellShine)" opacity="0.52" transform="rotate(18 104 104)" />
        <ellipse cx="130" cy="164" rx="83" ry="112" fill="none" stroke="rgba(127,64,21,0.24)" strokeWidth="2" />
        <g className="embryo-visual__veins">
          {veinAngles.map((angle, index) => (
            <path
              key={angle}
              d={`M130 174 C ${122 - index * 2} ${146 - index * 3}, ${104 + index * 5} ${132 + index * 6}, ${88 + index * 4} ${116 + index * 3}`}
              fill="none"
              stroke="rgba(171,52,47,0.42)"
              strokeLinecap="round"
              strokeWidth="2"
              transform={`rotate(${angle} 130 174)`}
            />
          ))}
        </g>
        <g className="embryo-visual__body" style={{ "--embryo-scale": String(stage.scale) } as CSSProperties}>
          <path
            d="M130 150 C163 128 188 157 176 190 C165 221 121 232 96 207 C76 186 84 158 108 151 C116 148 123 148 130 150Z"
            fill="url(#embryoGlow)"
          />
          <path
            d="M146 177 C133 175 121 185 119 199 C117 213 128 223 143 219"
            fill="none"
            stroke="rgba(91,28,33,0.52)"
            strokeLinecap="round"
            strokeWidth="6"
          />
          <circle cx="150" cy="163" r="5" fill="#3b1d24" opacity={active.current_day > 3 ? 1 : 0.25} />
          <path
            d="M104 190 C88 197 84 210 92 222"
            fill="none"
            stroke="rgba(91,28,33,0.4)"
            strokeLinecap="round"
            strokeWidth="5"
            opacity={progress > 35 ? 1 : 0.25}
          />
          <path
            d="M166 197 C180 206 181 221 171 232"
            fill="none"
            stroke="rgba(91,28,33,0.35)"
            strokeLinecap="round"
            strokeWidth="5"
            opacity={progress > 55 ? 1 : 0.15}
          />
        </g>
        {shellCracks && (
          <path d="M172 47 l-12 22 l17 7 l-15 19 l14 12" fill="none" stroke="rgba(98,56,24,0.48)" strokeLinecap="round" strokeWidth="4" />
        )}
      </svg>
      <div className="embryo-visual__shine" />
    </div>
  );
}

function HatchCountdown({ active }: { active: ActiveIncubation | null }) {
  if (!active) {
    return (
      <Card className="overflow-hidden">
        <CardContent className="flex min-h-72 items-center justify-center text-center">
          <div>
            <p className="text-2xl font-semibold">No active incubation profile</p>
            <p className="mt-2 text-sm text-foreground/60">Save a profile to start the hatch countdown.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const stage = embryoStage(active);
  const progress = Math.min(100, Math.max(0, active.progress_percent));
  const progressDegrees = progress * 3.6;

  return (
    <Card className="overflow-hidden">
      <CardContent className="grid gap-6 p-0 lg:grid-cols-[minmax(280px,0.9fr)_minmax(320px,1.1fr)]">
        <div className="relative min-h-[330px] bg-[radial-gradient(circle_at_28%_20%,rgba(245,158,11,0.22),transparent_32%),linear-gradient(135deg,rgba(20,184,166,0.16),rgba(244,114,182,0.12))] p-5">
          <EmbryoDayVisual active={active} />
        </div>
        <div className="flex flex-col justify-center gap-6 p-5">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
            <div
              className="grid h-36 w-36 shrink-0 place-items-center rounded-full"
              style={{ background: `conic-gradient(hsl(var(--primary)) ${progressDegrees}deg, hsl(var(--muted)) 0deg)` }}
            >
              <div className="grid h-28 w-28 place-items-center rounded-full bg-card text-center shadow-panel">
                <div>
                  <p className="text-3xl font-bold">{active.days_remaining}</p>
                  <p className="text-xs uppercase tracking-wide text-foreground/60">days left</p>
                </div>
              </div>
            </div>
            <div>
              <p className="text-sm font-medium uppercase tracking-wide text-primary">Day {active.current_day} of {active.incubation_days}</p>
              <h2 className="mt-2 text-3xl font-semibold">{stage.name}</h2>
              <p className="mt-2 max-w-xl text-sm leading-6 text-foreground/65">{stage.detail}</p>
            </div>
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-muted">
            <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${progress}%` }} />
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-md border border-border p-3">
              <p className="text-xs uppercase tracking-wide text-foreground/55">Expected Hatch</p>
              <p className="mt-1 font-semibold">{new Date(active.expected_hatch_date).toLocaleDateString()}</p>
            </div>
            <div className="rounded-md border border-border p-3">
              <p className="text-xs uppercase tracking-wide text-foreground/55">Progress</p>
              <p className="mt-1 font-semibold">{progress.toFixed(1)}%</p>
            </div>
            <div className="rounded-md border border-border p-3">
              <p className="text-xs uppercase tracking-wide text-foreground/55">Turning</p>
              <p className="mt-1 font-semibold">{active.turning_enabled_today ? "Enabled" : "Stopped"}</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function IncubationProfile() {
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [profileId, setProfileId] = useState<number | null>(null);
  const [active, setActive] = useState<Awaited<ReturnType<typeof incubatorApi.incubation>>["active"]>(null);
  const [form, setForm] = useState<ProfileForm>(emptyForm());

  const load = async () => {
    setLoading(true);
    const payload = await incubatorApi.incubation();
    setActive(payload.active);
    if (payload.active) {
      setProfileId(payload.active.id);
      setForm({
        bird_category: payload.active.bird_category,
        custom_bird: payload.active.custom_bird ?? "",
        batch_name: payload.active.batch_name,
        egg_count: payload.active.egg_count,
        loading_date: payload.active.loading_date,
        incubation_days: payload.active.incubation_days,
        lockdown_day: payload.active.lockdown_day,
        target_temperature: payload.active.target_temperature,
        target_humidity: payload.active.target_humidity,
        turning_enabled: payload.active.turning_enabled,
        turning_disabled_day: payload.active.turning_disabled_day,
        notes: payload.active.notes,
        is_active: payload.active.is_active
      });
    }
    setLoading(false);
  };

  useEffect(() => {
    load().catch(console.error);
  }, []);

  const setBird = (bird: string) => {
    setForm({ ...form, bird_category: bird, ...(defaults[bird] ?? defaults.custom) });
  };

  const save = async (event: FormEvent) => {
    event.preventDefault();
    const payload = { ...form, custom_bird: form.bird_category === "custom" ? form.custom_bird : null };
    if (profileId) {
      await incubatorApi.updateIncubation(profileId, payload as never);
    } else {
      await incubatorApi.saveIncubation(payload as never);
    }
    toast("Incubation profile saved");
    await load();
  };

  if (loading) return <Skeleton className="h-[70vh] w-full" />;

  return (
    <form className="space-y-6" onSubmit={save}>
      <HatchCountdown active={active} />
      <div className="grid gap-4 md:grid-cols-3">
        <StatusCard label="Current Day" value={active ? `Day ${active.current_day}` : "Not set"} icon={<CalendarDays />} />
        <StatusCard label="Expected Hatch" value={active ? new Date(active.expected_hatch_date).toLocaleDateString() : "--"} />
        <StatusCard label="Progress" value={active ? `${active.progress_percent}%` : "--"} />
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Incubation Profile</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <label className="space-y-2 text-sm">
            Bird category
            <Select value={form.bird_category} onChange={(event) => setBird(event.target.value)}>
              <option value="chicken">Chicken</option>
              <option value="duck">Duck</option>
              <option value="quail">Quail</option>
              <option value="turkey">Turkey</option>
              <option value="goose">Goose</option>
              <option value="custom">Custom</option>
            </Select>
          </label>
          {form.bird_category === "custom" && (
            <label className="space-y-2 text-sm">Custom bird<Input value={form.custom_bird} onChange={(event) => setForm({ ...form, custom_bird: event.target.value })} /></label>
          )}
          <label className="space-y-2 text-sm">Batch name<Input value={form.batch_name} onChange={(event) => setForm({ ...form, batch_name: event.target.value })} /></label>
          <label className="space-y-2 text-sm">Egg count<Input type="number" value={form.egg_count} onChange={(event) => setForm({ ...form, egg_count: Number(event.target.value) })} /></label>
          <label className="space-y-2 text-sm">Loading date<Input type="date" value={form.loading_date} onChange={(event) => setForm({ ...form, loading_date: event.target.value })} /></label>
          <label className="space-y-2 text-sm">Incubation days<Input type="number" value={form.incubation_days} onChange={(event) => setForm({ ...form, incubation_days: Number(event.target.value) })} /></label>
          <label className="space-y-2 text-sm">Lockdown day<Input type="number" value={form.lockdown_day} onChange={(event) => setForm({ ...form, lockdown_day: Number(event.target.value) })} /></label>
          <label className="space-y-2 text-sm">Stop turning day<Input type="number" value={form.turning_disabled_day} onChange={(event) => setForm({ ...form, turning_disabled_day: Number(event.target.value) })} /></label>
          <label className="space-y-2 text-sm">Target temperature<Input type="number" step="0.1" value={form.target_temperature} onChange={(event) => setForm({ ...form, target_temperature: Number(event.target.value) })} /></label>
          <label className="space-y-2 text-sm">Target humidity<Input type="number" step="0.1" value={form.target_humidity} onChange={(event) => setForm({ ...form, target_humidity: Number(event.target.value) })} /></label>
          <label className="flex items-center gap-3 text-sm md:col-span-2">
            <input type="checkbox" checked={form.turning_enabled} onChange={(event) => setForm({ ...form, turning_enabled: event.target.checked })} />
            Enable tray turning for this profile
          </label>
          <label className="space-y-2 text-sm md:col-span-2">
            Notes
            <textarea className="min-h-24 w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary" value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} />
          </label>
        </CardContent>
      </Card>
      <Button type="submit"><Save size={18} /> Save Profile</Button>
    </form>
  );
}
