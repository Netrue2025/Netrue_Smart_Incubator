import { CheckCircle2, CheckSquare, Mail, Send, Square, Trash2, X } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { incubatorApi } from "../api/client";
import { useToast } from "../components/Toast";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { formatTime } from "../lib/utils";
import { useIncubatorStore } from "../store/incubator";
import type { NotificationSettings } from "../types/incubator";

type NotificationForm = NotificationSettings & {
  telegram_bot_token: string;
  smtp_password: string;
};

const blankNotifications: NotificationForm = {
  telegram_enabled: false,
  telegram_chat_id: "",
  telegram_bot_token: "",
  telegram_bot_token_set: false,
  email_enabled: false,
  email_to: "",
  email_from: "",
  smtp_host: "",
  smtp_port: 587,
  smtp_username: "",
  smtp_password: "",
  smtp_password_set: false,
  smtp_use_tls: true
};

export function Alerts() {
  const { alerts, loadAlerts } = useIncubatorStore();
  const toast = useToast();
  const [selected, setSelected] = useState<number[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [notificationForm, setNotificationForm] = useState<NotificationForm>(blankNotifications);

  useEffect(() => {
    loadAlerts().catch(console.error);
    incubatorApi.notificationSettings().then((settings) => setNotificationForm({ ...blankNotifications, ...settings, telegram_bot_token: "", smtp_password: "" })).catch(console.error);
  }, [loadAlerts]);

  const selectedSet = new Set(selected);
  const toggle = (id: number) => {
    setSelected((items) => (items.includes(id) ? items.filter((item) => item !== id) : [...items, id]));
  };
  const toggleAll = () => {
    setSelected(selected.length === alerts.length ? [] : alerts.map((alert) => alert.id));
  };
  const ack = async (id: number) => {
    await incubatorApi.ackAlert(id);
    toast("Alert acknowledged");
    await loadAlerts();
  };
  const deleteSelected = async () => {
    if (selected.length === 0) {
      toast("Select alert history to delete");
      return;
    }
    if (!confirm(`Delete ${selected.length} selected alert(s)?`)) return;
    await incubatorApi.deleteAlerts(selected);
    setSelected([]);
    toast("Selected alerts deleted");
    await loadAlerts();
  };
  const saveNotifications = async (event: FormEvent) => {
    event.preventDefault();
    const saved = await incubatorApi.saveNotificationSettings(notificationForm);
    setNotificationForm({ ...blankNotifications, ...saved, telegram_bot_token: "", smtp_password: "" });
    setModalOpen(false);
    toast("Alert notification settings saved");
  };

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <CardTitle>Alerts</CardTitle>
            <div className="flex flex-wrap gap-2">
              <Button type="button" className="bg-muted text-foreground" onClick={() => setModalOpen(true)} title="Telegram and email alert settings">
                <Send size={18} /> <Mail size={18} />
              </Button>
              <Button type="button" className="bg-muted text-foreground" onClick={toggleAll}>
                {selected.length === alerts.length && alerts.length > 0 ? <CheckSquare size={18} /> : <Square size={18} />} Select
              </Button>
              <Button type="button" className="bg-destructive" onClick={deleteSelected}>
                <Trash2 size={18} /> Delete
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {alerts.map((alert) => (
            <div key={alert.id} className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-border p-4">
              <div className="flex min-w-0 flex-1 items-start gap-3">
                <button type="button" className="mt-1 text-foreground/70" onClick={() => toggle(alert.id)} title="Select alert">
                  {selectedSet.has(alert.id) ? <CheckSquare size={18} /> : <Square size={18} />}
                </button>
                <div>
                  <p className="font-semibold capitalize">{alert.type.replaceAll("_", " ")}</p>
                  <p className="text-sm text-foreground/70">{alert.message}</p>
                  <p className="text-xs text-foreground/50">{formatTime(alert.created_at)} - {alert.severity}</p>
                </div>
              </div>
              {!alert.acknowledged && (
                <Button type="button" onClick={() => ack(alert.id)}>
                  <CheckCircle2 size={18} /> Acknowledge
                </Button>
              )}
            </div>
          ))}
          {alerts.length === 0 && <p className="text-sm text-foreground/60">No alerts recorded.</p>}
        </CardContent>
      </Card>

      {modalOpen ? (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4">
          <form className="max-h-[90vh] w-full max-w-3xl overflow-auto rounded-md border border-border bg-card p-5 shadow-panel" onSubmit={saveNotifications}>
            <div className="mb-4 flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold">Alert Notifications</h2>
              <button type="button" title="Close" onClick={() => setModalOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="grid gap-5 md:grid-cols-2">
              <div className="space-y-4 rounded-md border border-border p-4">
                <div className="flex items-center gap-2 font-semibold"><Send size={18} /> Telegram</div>
                <label className="flex items-center gap-3 text-sm">
                  <input type="checkbox" checked={notificationForm.telegram_enabled} onChange={(event) => setNotificationForm({ ...notificationForm, telegram_enabled: event.target.checked })} />
                  Enable Telegram alerts
                </label>
                <label className="space-y-2 text-sm">Chat ID<Input value={notificationForm.telegram_chat_id} onChange={(event) => setNotificationForm({ ...notificationForm, telegram_chat_id: event.target.value })} /></label>
                <label className="space-y-2 text-sm">
                  Bot token
                  <Input type="password" placeholder={notificationForm.telegram_bot_token_set ? "Saved token unchanged unless replaced" : ""} value={notificationForm.telegram_bot_token} onChange={(event) => setNotificationForm({ ...notificationForm, telegram_bot_token: event.target.value })} />
                </label>
              </div>

              <div className="space-y-4 rounded-md border border-border p-4">
                <div className="flex items-center gap-2 font-semibold"><Mail size={18} /> Email</div>
                <label className="flex items-center gap-3 text-sm">
                  <input type="checkbox" checked={notificationForm.email_enabled} onChange={(event) => setNotificationForm({ ...notificationForm, email_enabled: event.target.checked })} />
                  Enable email alerts
                </label>
                <label className="space-y-2 text-sm">Target email<Input type="email" value={notificationForm.email_to} onChange={(event) => setNotificationForm({ ...notificationForm, email_to: event.target.value })} /></label>
                <label className="space-y-2 text-sm">From email<Input type="email" value={notificationForm.email_from} onChange={(event) => setNotificationForm({ ...notificationForm, email_from: event.target.value })} /></label>
                <label className="space-y-2 text-sm">SMTP host<Input value={notificationForm.smtp_host} onChange={(event) => setNotificationForm({ ...notificationForm, smtp_host: event.target.value })} /></label>
                <label className="space-y-2 text-sm">SMTP port<Input type="number" value={notificationForm.smtp_port} onChange={(event) => setNotificationForm({ ...notificationForm, smtp_port: Number(event.target.value) })} /></label>
                <label className="space-y-2 text-sm">SMTP username<Input value={notificationForm.smtp_username} onChange={(event) => setNotificationForm({ ...notificationForm, smtp_username: event.target.value })} /></label>
                <label className="space-y-2 text-sm">
                  SMTP password
                  <Input type="password" placeholder={notificationForm.smtp_password_set ? "Saved password unchanged unless replaced" : ""} value={notificationForm.smtp_password} onChange={(event) => setNotificationForm({ ...notificationForm, smtp_password: event.target.value })} />
                </label>
                <label className="flex items-center gap-3 text-sm">
                  <input type="checkbox" checked={notificationForm.smtp_use_tls} onChange={(event) => setNotificationForm({ ...notificationForm, smtp_use_tls: event.target.checked })} />
                  Use STARTTLS
                </label>
              </div>
            </div>
            <div className="mt-5 flex justify-end gap-3">
              <Button type="button" className="bg-muted text-foreground" onClick={() => setModalOpen(false)}>Cancel</Button>
              <Button type="submit">Save Notifications</Button>
            </div>
          </form>
        </div>
      ) : null}
    </>
  );
}
