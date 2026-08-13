# safari extractor

Parses Safari history (`History.db` and related) from an MVT-decrypted
backup and writes normalized `forensic_records` rows with
`source_type: safari_history`.

## Status
Not yet built — awaiting source material. Once shared, document here:
- Expected input path/file(s) within the backup
- The `fields` (JSONB) shape this extractor owns
- Chosen partial-failure behavior (see /contracts/EXTRACTOR_CONTRACT.md §5)

## Suggested fields shape (draft, confirm once source data is in hand)
```
{
  "url": ...,
  "title": ...,
  "visit_count": ...,
  "last_visit_time": ...,   -- also becomes the record's top-level event_time
  "redirect_source": ...
}
```
