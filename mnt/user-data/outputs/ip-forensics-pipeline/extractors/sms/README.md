# sms extractor

Parses SMS/iMessage attachments and metadata from an MVT-decrypted backup
and writes normalized `forensic_records` rows with
`source_type: sms_attachment`.

## Status
Not yet built — awaiting source material. Once shared, document here:
- Expected input path/file(s) within the backup
- The `fields` (JSONB) shape this extractor owns
- Chosen partial-failure behavior — this is a strong candidate for
  per-attachment isolation (one corrupt attachment shouldn't block the rest
  of the thread), per /contracts/EXTRACTOR_CONTRACT.md §5

## Suggested fields shape (draft, confirm once source data is in hand)
```
{
  "thread_id": ...,
  "sender": ...,
  "attachment_type": ...,
  "attachment_path": ...,
  "message_text_excerpt": ...   -- consider redaction/truncation policy
}
```
