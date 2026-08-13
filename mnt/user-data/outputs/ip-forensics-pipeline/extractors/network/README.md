# network extractor

Parses network data usage records from an MVT-decrypted backup and writes
normalized `forensic_records` rows with `source_type: network_usage`.

## Status
Not yet built — awaiting source material. Once shared, document here:
- Expected input path/file(s) within the backup
- The `fields` (JSONB) shape this extractor owns
- Chosen partial-failure behavior (see /contracts/EXTRACTOR_CONTRACT.md §5)

## Suggested fields shape (draft, confirm once source data is in hand)
```
{
  "bundle_id": ...,
  "bytes_in": ...,
  "bytes_out": ...,
  "interface": ...,    -- wifi/cellular
  "window_start": ..., "window_end": ...
}
```
