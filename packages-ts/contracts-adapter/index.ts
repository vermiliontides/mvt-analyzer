// contracts-adapter/index.ts
// Small adapter that exposes the canonical JSON schema to TypeScript runtimes.
// Consumers can import the schema and use their preferred validator (Ajv, Zod, etc.).

import schema from '../../../contracts/normalized-record.schema.json';

export const normalizedRecordSchema = schema as unknown;

// Helper: a very small typed interface matching the top-level envelope.
// This is intentionally shallow: detailed `fields` shapes are owned by each extractor.
export interface NormalizedRecord {
  incident_id?: string | null;
  source_type: string;
  event_time?: string | null; // ISO-8601
  bug_type?: string | null;
  process_name?: string | null;
  pid?: number | null;
  bundle_id?: string | null;
  fields: Record<string, any>;
}

// Validation helper stub: projects are free to wire Ajv or Zod. Example usage:
// import Ajv from 'ajv'; const ajv = new Ajv(); const validate = ajv.compile(normalizedRecordSchema);
// if (!validate(obj)) { console.error(validate.errors); }

export default {
  normalizedRecordSchema,
};
