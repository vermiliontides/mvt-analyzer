/**
 * Zod mirror of normalized-record.schema.json.
 *
 * Used by orchestrator/ and reporting/ (and any future TS extractor) so a
 * record read out of Postgres — or about to be written into it — is
 * validated against the exact same envelope Python extractors build against.
 *
 * Keep this in lockstep with:
 *   - contracts/normalized-record.schema.json  (source of truth)
 *   - contracts/normalized_record.py           (Python/Pydantic mirror)
 */

import { z } from "zod";

export const SourceType = z.enum([
  "crash_report",
  "siri_feedback",
  "sfa_analytics",
  "xp_amp_telemetry",
  "safari_history",
  "sms_attachment",
  "network_usage",
  "gcloud_log",
  "syslog_line",
]);
export type SourceType = z.infer<typeof SourceType>;

export const NormalizedRecord = z
  .object({
    incident_id: z.string().nullable().default(null),
    source_type: SourceType,
    event_time: z.string().datetime().nullable().default(null),
    bug_type: z.string().nullable().default(null),
    process_name: z.string().nullable().default(null),
    pid: z.number().int().nullable().default(null),
    bundle_id: z.string().nullable().default(null),
    fields: z.record(z.string(), z.unknown()).default({}),
    raw_ref: z.string().nullable().default(null),
  })
  .strict();

export type NormalizedRecord = z.infer<typeof NormalizedRecord>;
