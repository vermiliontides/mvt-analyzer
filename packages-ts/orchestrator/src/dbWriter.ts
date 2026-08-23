import * as crypto from 'node:crypto';
import * as fs from 'node:fs/promises';
import type { Client, PoolClient } from 'pg';

import {
  NormalizedRecord as NormalizedRecordSchema,
  type NormalizedRecord as NormalizedRecordShape,
} from '../../contracts/normalizedRecord';

export const DEFAULT_DB_URL = 'postgresql://forensics:forensics_dev_only@localhost:5432/forensics';

export async function computeFileHash(filePath: string): Promise<string> {
  const buffer = await fs.readFile(filePath);
  return crypto.createHash('sha256').update(buffer).digest('hex');
}

export async function ingestFile(
  client: Client | PoolClient,
  runId: string,
  filePath: string,
  sourceType: string,
  rawPayload: Record<string, unknown>
): Promise<{ fileHash: string; alreadyIngested: boolean }> {
  const fileHash = await computeFileHash(filePath);

  const existing = await client.query(
    'SELECT 1 FROM ingested_files WHERE file_hash = $1 LIMIT 1',
    [fileHash]
  );

  if (existing.rowCount && existing.rowCount > 0) {
    return { fileHash, alreadyIngested: true };
  }

  await client.query(
    `INSERT INTO ingested_files
      (file_hash, run_id, file_path, file_name, source_type, raw_payload)
     VALUES ($1, $2, $3, $4, $5, $6)
     ON CONFLICT (file_hash) DO NOTHING`,
    [
      fileHash,
      runId,
      filePath,
      filePath.split(/[\\/]/).pop() ?? filePath,
      sourceType,
      rawPayload,
    ]
  );

  return { fileHash, alreadyIngested: false };
}

export async function writeRecord(
  client: Client | PoolClient,
  runId: string,
  fileHash: string,
  record: NormalizedRecordShape
): Promise<void> {
  const validated = NormalizedRecordSchema.parse(record);

  await client.query(
    `INSERT INTO forensic_records
      (file_hash, run_id, incident_id, source_type, event_time,
       bug_type, process_name, pid, bundle_id, fields)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)`,
    [
      fileHash,
      runId,
      validated.incident_id ?? null,
      validated.source_type,
      validated.event_time ?? null,
      validated.bug_type ?? null,
      validated.process_name ?? null,
      validated.pid ?? null,
      validated.bundle_id ?? null,
      validated.fields,
    ]
  );
}

export async function writeRecords(
  client: Client | PoolClient,
  runId: string,
  fileHash: string,
  records: NormalizedRecordShape[]
): Promise<number> {
  if (records.length === 0) {
    return 0;
  }

  const values: string[] = [];
  const params: unknown[] = [];

  records.forEach((record, index) => {
    const validated = NormalizedRecordSchema.parse(record);
    const base = index * 10;
    values.push(
      `($${base + 1}, $${base + 2}, $${base + 3}, $${base + 4}, $${base + 5}, $${base + 6}, $${base + 7}, $${base + 8}, $${base + 9}, $${base + 10})`
    );
    params.push(
      fileHash,
      runId,
      validated.incident_id ?? null,
      validated.source_type,
      validated.event_time ?? null,
      validated.bug_type ?? null,
      validated.process_name ?? null,
      validated.pid ?? null,
      validated.bundle_id ?? null,
      validated.fields
    );
  });

  await client.query(
    `INSERT INTO forensic_records
      (file_hash, run_id, incident_id, source_type, event_time,
       bug_type, process_name, pid, bundle_id, fields)
     VALUES ${values.join(', ')}`,
    params
  );

  return records.length;
}
