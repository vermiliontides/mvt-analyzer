# gcloud extractor

Parses decrypted gcloud logs and writes normalized `forensic_records` rows
with `source_type: gcloud_log`.

## Status
Not yet built — awaiting source material. Once shared, document here:
- Expected input path/file(s) or log export format
- The `fields` (JSONB) shape this extractor owns
- Chosen partial-failure behavior. Given this is likely the highest-volume
  source (multi-week window), see the row-per-line vs. pre-aggregated
  discussion in /docs/architecture.md before deciding — row-per-line is
  the current default recommendation for credibility/traceability.
