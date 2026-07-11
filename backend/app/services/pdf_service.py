from typing import Any


class PDFService:
    @staticmethod
    def report_payload(summary: dict[str, Any]) -> dict[str, Any]:
        return {
            "title": "Smart Incubator Power Report",
            "date": summary["rtc_time"],
            "summary": {
                "total_energy_used_wh": summary["energy_today_wh"],
                "last_hour_energy_wh": summary["energy_last_hour_wh"],
                "current_hour_energy_wh": summary["energy_current_hour_wh"],
                "last_completed_hour_label": summary["last_completed_hour_label"],
                "current_hour_label": summary["current_hour_label"],
            },
            "hourly_table": summary["hourly_history"],
        }
