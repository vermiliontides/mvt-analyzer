"""
Pydantic mirror of normalized-record.schema.json.

Every Python extractor imports NormalizedRecord from here and constructs one
per source record before writing to Postgres. This is what makes a new
extractor "additive" instead of risky — it can't drift from the shared
envelope because the type checker/validator enforces it at construction time,
not at report-render time (which is where the original crash-report bug
would have been caught, too late, if it had been caught at all).

Keep this in lockstep with:
  - contracts/normalized-record.schema.json  (source of truth)
  - contracts/normalizedRecord.ts            (TypeScript/Zod mirror)
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict


class SourceType(str, Enum):
    CRASH_REPORT = "crash_report"
    SIRI_FEEDBACK = "siri_feedback"
    SFA_ANALYTICS = "sfa_analytics"
    XP_AMP_TELEMETRY = "xp_amp_telemetry"
    SAFARI_HISTORY = "safari_history"
    SMS_ATTACHMENT = "sms_attachment"
    NETWORK_USAGE = "network_usage"
    GCLOUD_LOG = "gcloud_log"
    SYSLOG_LINE = "syslog_line"


class NormalizedRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident_id: str | None = None
    source_type: SourceType
    event_time: datetime | None = None
    bug_type: str | None = None
    process_name: str | None = None
    pid: int | None = None
    bundle_id: str | None = None
    fields: dict[str, Any] = {}
    raw_ref: str | None = None  # file_hash back-reference into ingested_files
