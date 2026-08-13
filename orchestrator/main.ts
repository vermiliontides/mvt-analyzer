/**
 * orchestrator/main.ts
 *
 * Conductor for a full investigation run. Creates a pipeline_run, invokes
 * each extractor as an isolated subprocess stage, records per-stage status,
 * and — critically — NEVER lets one stage's failure abort the others.
 *
 * This file intentionally does not know how to parse any source format.
 * That's the extractors' job (see /extractors/*, /contracts/EXTRACTOR_CONTRACT.md).
 * This file only knows how to run a stage, record what happened, and move on.
 */

import { spawn } from "node:child_process";
import { Client } from "pg";
import { randomUUID } from "node:crypto";

interface StageDefinition {
  name: string;
  /** Executable + args to invoke this stage. Extends with --run-id/--backup-path/--db-url at call time. */
  command: string;
  args: string[];
}

// TODO: fill in real entrypoints as each extractor is added under /extractors.
// Order matters only in that "report" must run last — extractors themselves
// are independent and could run concurrently later if that ever becomes a
// bottleneck (see /docs/architecture.md for why we're not doing that yet).
const STAGES: StageDefinition[] = [
  { name: "crash", command: "python3", args: ["../extractors/crash/main.py"] },
  { name: "safari", command: "python3", args: ["../extractors/safari/main.py"] },
  { name: "sms", command: "python3", args: ["../extractors/sms/main.py"] },
  { name: "network", command: "python3", args: ["../extractors/network/main.py"] },
  { name: "gcloud", command: "python3", args: ["../extractors/gcloud/main.py"] },
  { name: "report", command: "python3", args: ["../reporting/generate_report.py"] },
];

interface RunConfig {
  backupPath: string;
  dbUrl: string;
}

async function createRun(client: Client, backupPath: string): Promise<string> {
  const runId = randomUUID();
  await client.query(
    `INSERT INTO pipeline_runs (run_id, backup_source) VALUES ($1, $2)`,
    [runId, backupPath]
  );
  for (const stage of STAGES) {
    await client.query(
      `INSERT INTO pipeline_stage_status (run_id, stage_name, status) VALUES ($1, $2, 'pending')`,
      [runId, stage.name]
    );
  }
  return runId;
}

async function markStage(
  client: Client,
  runId: string,
  stageName: string,
  status: "running" | "succeeded" | "failed",
  errorMessage?: string
): Promise<void> {
  const timestampCol = status === "running" ? "started_at" : "finished_at";
  await client.query(
    `UPDATE pipeline_stage_status
     SET status = $1, error_message = $2, ${timestampCol} = now()
     WHERE run_id = $3 AND stage_name = $4`,
    [status, errorMessage ?? null, runId, stageName]
  );
}

/**
 * Runs one stage as a subprocess. Resolves regardless of outcome —
 * failure is communicated via the returned status, never via a thrown
 * error, because a thrown error here is exactly the thing that would
 * take down the rest of the run.
 */
function runStage(
  stage: StageDefinition,
  config: RunConfig,
  runId: string
): Promise<{ success: boolean; stderr: string }> {
  return new Promise((resolve) => {
    const child = spawn(
      stage.command,
      [...stage.args, "--run-id", runId, "--backup-path", config.backupPath, "--db-url", config.dbUrl],
      { stdio: ["ignore", "pipe", "pipe"] }
    );

    let stderr = "";
    child.stderr?.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    child.on("error", (err) => {
      // e.g. entrypoint doesn't exist yet — still don't throw, just report it
      resolve({ success: false, stderr: err.message });
    });

    child.on("close", (code) => {
      resolve({ success: code === 0, stderr: stderr.trim() });
    });
  });
}

async function main() {
  const backupPath = process.argv[2];
  if (!backupPath) {
    console.error("Usage: main.ts <path-to-decrypted-backup>");
    process.exit(1);
  }

  const dbUrl = process.env.DATABASE_URL ?? "postgresql://localhost:5432/forensics";
  const client = new Client({ connectionString: dbUrl });
  await client.connect();

  const runId = await createRun(client, backupPath);
  console.log(`[orchestrator] run ${runId} started against ${backupPath}`);

  const results: { stage: string; success: boolean }[] = [];

  for (const stage of STAGES) {
    console.log(`[orchestrator] -> ${stage.name}`);
    await markStage(client, runId, stage.name, "running");

    const { success, stderr } = await runStage(stage, { backupPath, dbUrl }, runId);

    if (success) {
      await markStage(client, runId, stage.name, "succeeded");
      console.log(`[orchestrator]    ${stage.name} succeeded`);
    } else {
      await markStage(client, runId, stage.name, "failed", stderr || "unknown error");
      console.error(`[orchestrator]    ${stage.name} FAILED — continuing to next stage`);
      if (stderr) console.error(`[orchestrator]    ${stderr}`);
    }

    results.push({ stage: stage.name, success });
  }

  await client.query(`UPDATE pipeline_runs SET finished_at = now() WHERE run_id = $1`, [runId]);
  await client.end();

  const failed = results.filter((r) => !r.success);
  console.log("\n[orchestrator] run complete");
  console.log(`  run_id: ${runId}`);
  console.log(`  succeeded: ${results.length - failed.length}/${results.length}`);
  if (failed.length > 0) {
    console.log(`  failed stages: ${failed.map((f) => f.stage).join(", ")}`);
    console.log(`  -> the report will note these as unavailable; fix and re-run the pipeline`);
    console.log(`     against the same backup to fill them in (idempotent, no need to redo successful stages).`);
  }
}

main().catch((err) => {
  // This top-level catch is a last resort — it should only ever fire for
  // infrastructure problems (e.g. can't reach Postgres at all), never for
  // a single extractor's failure, which is handled per-stage above.
  console.error("[orchestrator] fatal error outside stage handling:", err);
  process.exit(1);
});
