from datetime import datetime, timezone
from io import BytesIO, StringIO
from typing import Any

from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.models.entities import Report
from app.services.power_service import PowerService


def _pdf_bytes(title: str, lines: list[str]) -> bytes:
    text = "\\n".join([title, *lines]).replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 760 Td ({text}) Tj ET"
    objects = [
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj",
        "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
        f"5 0 obj << /Length {len(stream)} >> stream\n{stream}\nendstream endobj",
    ]
    body = "%PDF-1.4\n" + "\n".join(objects) + "\n"
    offsets = [0]
    cursor = len("%PDF-1.4\n")
    for obj in objects:
        offsets.append(cursor)
        cursor += len(obj) + 1
    xref_start = len(body)
    xref = "xref\n0 6\n0000000000 65535 f \n" + "".join(f"{offset:010d} 00000 n \n" for offset in offsets[1:])
    trailer = f"trailer << /Root 1 0 R /Size 6 >>\nstartxref\n{xref_start}\n%%EOF"
    return (body + xref + trailer).encode("utf-8")


def record_report(db: Session, report_type: str, payload: dict[str, Any]) -> Report:
    report = Report(report_type=report_type, metadata_json=str(payload), download_count=1)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def power_report_response(db: Session, export_format: str) -> StreamingResponse:
    summary = PowerService.summary(db, log=False)
    report = record_report(db, f"power_{export_format}", {"generated_at": datetime.now(timezone.utc).isoformat()})
    filename = f"power-report-{report.id}.{export_format}"
    rows = [
        ("Metric", "Value"),
        ("Total kWh", summary.get("total_kwh")),
        ("Energy Today Wh", summary.get("energy_today_wh")),
        ("Live Load Watts", summary.get("live_load_watts")),
        ("Heater Runtime Minutes", summary.get("heater_runtime_minutes")),
    ]
    if export_format == "pdf":
        payload = _pdf_bytes("Smart Incubator Power Report", [f"{key}: {value}" for key, value in rows[1:]])
        return StreamingResponse(BytesIO(payload), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    if export_format == "xlsx":
        output = StringIO()
        output.write("\n".join("\t".join(str(cell) for cell in row) for row in rows))
        return StreamingResponse(
            BytesIO(output.getvalue().encode("utf-8")),
            media_type="application/vnd.ms-excel",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    output = StringIO()
    output.write("\n".join(",".join(str(cell) for cell in row) for row in rows))
    return StreamingResponse(
        BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
