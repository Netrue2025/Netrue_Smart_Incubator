export type RelayMode = "AUTO" | "MANUAL" | "EMERGENCY_OFF";

export interface Reading {
  id?: number;
  temperature: number;
  humidity: number;
  heat_index: number;
  relay: boolean;
  fan_relay: boolean;
  wifi: boolean;
  sync_status: string;
  timestamp?: string;
  device_timestamp?: string;
  created_at?: string;
}

export interface Settings {
  id: number;
  device_name: string;
  timezone: string;
  target_temperature: number;
  target_humidity: number;
  tolerance: number;
  hysteresis: number;
  sampling_interval: number;
  sync_interval: number;
  temperature_offset: number;
  humidity_offset: number;
  relay_mode: RelayMode;
  manual_relay: boolean;
  emergency_off: boolean;
  tray_servo_enabled: boolean;
  tray_servo_angle: number;
  tray_servo_interval_minutes: number;
  tray_servo_speed_dps: number;
  wifi_ssid: string | null;
  wifi_password_set: boolean;
  wifi_scan_requested: boolean;
  wifi_connect_requested: boolean;
  wifi_active_ssid: string | null;
  wifi_ip_address: string | null;
  wifi_rssi: number | null;
  wifi_connection_status: string;
  wifi_last_scan_at: string | null;
  wifi_last_connect_at: string | null;
  updated_at: string;
}

export interface Alert {
  id: number;
  type: string;
  severity: "info" | "warning" | "critical";
  message: string;
  acknowledged: boolean;
  created_at: string;
}

export interface NotificationSettings {
  telegram_enabled: boolean;
  telegram_chat_id: string;
  telegram_bot_token_set: boolean;
  email_enabled: boolean;
  email_to: string;
  email_from: string;
  smtp_host: string;
  smtp_port: number;
  smtp_username: string;
  smtp_password_set: boolean;
  smtp_use_tls: boolean;
}

export interface StatusSnapshot {
  device: {
    online: boolean;
    name: string;
    last_sync: string | null;
    wifi: boolean;
    sync_status: string;
    wifi_ssid?: string | null;
    wifi_ip_address?: string | null;
    wifi_rssi?: number | null;
    wifi_connection_status?: string;
  };
  backend: {
    online: boolean;
    database: string;
    readings: number;
    queue_size: number;
  };
  environment: Reading | null;
  settings: Settings;
  time: string;
}

export interface WifiNetwork {
  id: number;
  ssid: string;
  rssi: number;
  encryption: string;
  channel: number | null;
  last_seen_at: string;
}

export interface HistoryPayload {
  readings: Reading[];
  relay: Array<{ id: number; relay: boolean; mode: RelayMode; reason: string; created_at: string }>;
}

export interface IncubationProfile {
  id: number;
  bird_category: string;
  custom_bird: string | null;
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
  created_at: string;
  updated_at: string;
  current_day: number;
  days_remaining: number;
  progress_percent: number;
  expected_hatch_date: string;
  lockdown_date: string;
  turning_enabled_today: boolean;
}

export interface IncubationPayload {
  active: IncubationProfile | null;
  profiles: IncubationProfile[];
}

export interface ServoAnalytics {
  enabled: boolean;
  target_angle: number;
  interval_minutes: number;
  speed_dps: number;
  next_turn_at: string | null;
  seconds_to_next_turn: number | null;
  next_target_angle: number | null;
  expected_cycles_per_day: number;
  completed_today: number;
  failures_today: number;
  failure_reasons: Array<{ id: number; message: string; target_angle: number; created_at: string }>;
  profile_turning_enabled: boolean;
  last_event: {
    id: number;
    event_type: string;
    success: boolean;
    target_angle: number;
    duration_seconds: number;
    message: string;
    created_at: string;
  } | null;
}

export interface HeaterAnalytics {
  window_hours: number;
  cycles: number;
  runtime_seconds: number;
  runtime_minutes: number;
  duty_cycle_percent: number;
  currently_on: boolean;
  average_temperature: number | null;
  min_temperature: number | null;
  max_temperature: number | null;
  recent_events: Array<{ id: number; relay: boolean; mode: string; reason: string; created_at: string }>;
}

export interface PowerSummary {
  config: {
    heater_watts: number;
    fan_watts: number;
    controller_watts: number;
    servo_watts: number;
    servo_average_watts: number;
    lcd_watts: number;
    relay_watts: number;
    dht22_watts: number;
    buzzer_watts: number;
    grid_voltage: number;
    tariff_per_kwh: number;
    battery_backup_enabled: boolean;
    battery_voltage: number;
    battery_capacity_ah: number;
    battery_charge_percent: number;
    battery_health_percent: number;
    battery_usable_percent: number;
    inverter_efficiency_percent: number;
    battery_chemistry: string;
    updated_at: string;
  };
  window_hours: number;
  selected_date: string;
  is_today: boolean;
  day_start: string;
  day_end: string;
  heater_kwh: number;
  base_kwh: number;
  servo_kwh: number;
  total_kwh: number;
  estimated_cost: number;
  estimated_current_amps: number;
  heater_runtime_minutes: number;
  heater_cycles: number;
  live_load_watts: number;
  average_load_watts: number;
  peak_load_watts: number;
  energy_last_hour_wh: number;
  energy_current_hour_wh: number;
  energy_today_wh: number;
  heater_duty_last_hour_percent: number;
  heater_duty_current_hour_percent: number;
  last_completed_hour_start: string;
  last_completed_hour_end: string;
  last_completed_hour_label: string;
  current_hour_start: string;
  current_hour_label: string;
  rtc_time: string;
  battery: {
    energy_wh: number;
    runtime_hours: number | null;
    recharge_before: string | null;
    severity: "ok" | "warning" | "critical" | "unknown";
    basis_average_watts?: number;
    sample_count?: number;
    confidence?: "ok" | "low";
  };
  recharge_before: string | null;
  live: {
    heater_state: "ON" | "OFF";
    heater_on: boolean;
    heater_on_time: string | null;
    heater_off_time: string | null;
    temperature: number | null;
    humidity: number | null;
    fan_on: boolean;
    servo_status: string;
    servo_active: boolean;
    buzzer_active: boolean;
  };
  hourly_history: Array<{
    hour: string;
    created_at: string;
    energy_wh: number;
    average_load_watts: number;
    heater_duty_percent: number;
    battery_percent: number;
  }>;
  report: {
    title: string;
    date: string;
    battery: PowerSummary["config"];
    summary: {
      total_energy_used_wh: number;
      average_load_watts: number;
      peak_load_watts: number;
      average_heater_duty_percent: number;
      last_hour_energy_wh?: number;
      current_hour_energy_wh?: number;
      last_completed_hour_label?: string;
      current_hour_label?: string;
      estimated_runtime_hours: number | null;
    };
    hourly_table: PowerSummary["hourly_history"];
  };
}

export interface SystemHealth {
  state: "ok" | "warning" | "critical";
  score: number;
  checked_at: string;
  unacknowledged_alerts: number;
  queue_size: number;
  modules: Array<{ module: string; state: "ok" | "warning" | "critical" | "idle"; detail: string }>;
}
