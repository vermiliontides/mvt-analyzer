/**
 * packages-ts/orchestrator/main-orchestrator/main.ts
 *
 * Conductor for a full investigation run. Creates a pipeline_run PER BACKUP,
 * invokes each extractor as an isolated subprocess stage, records per-stage
 * status, and — critically — NEVER lets one stage's (or one backup's)
 * failure abort the others.
 *
 * This file intentionally does not know how to parse any source format.
 * That's the extractors' job (see /extractors/*, /contracts/EXTRACTOR_CONTRACT.md).
 * This file only knows how to run a stage, record what happened, and move on.
 *
 * Multi-backup note: mvt-runner (../mvt-runner) is the upstream tool that
 * decrypts a directory of raw iPhone backups into
 * <workspace>/decrypted/<name>/, one directory per backup, prompting
 * interactively for each backup's password as it goes. By the time this
 * orchestrator runs, that's already done — every backup it processes here
 * is decrypted and sitting on disk. There is no interactivity to reconcile
 * at this layer; the only real gap was that this file used to assume a
 * single --backup-path. It now accepts N backups and runs a full,
 * independent pipeline against each — one failing backup (or one failing
 * stage within a backup) never blocks the others.
 *
 * --results-path note: every stage is now also given a best-effort
 * --results-path (<workspace>/results/<name>/, mvt-runner's sibling
 * directory to decrypted/<name>/), derived from --backup-path. This is a
 * no-op for extractors that don't need it (safari/sms/network parse the
 * decrypted backup, not mvt-ios's output — see EXTRACTOR_CONTRACT.md's
 * Option A rationale) and required for extractors/mvt_iocs, which reads
 * mvt-ios's own alerts.json/timeline.csv as primary evidence. If a
 * results/ dir can't be derived (e.g. an explicit non-workspace backup
 * path with no 'decrypted' segment), it's simply omitted — extractors
 * that need it fail with their own clear error rather than the
 * orchestrator guessing.
 */

import { spawn } from "node:child_process";
import { Client } from "pg";
import { randomUUID } from "node:crypto";
import { parseArgs } from "node:util";
import * as fsp from "node:fs/promises";
import * as path from "node:path";

interface StageDefinition {
  name: string;
  /** Executable + args to invoke this stage. Extends with --run-id/--backup-path/--results-path/--db-url at call time. */
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
  { name: "mvt_iocs", command: "python3", args: ["../extractors/mvt_iocs/main.py"] },
  { name: "report", command: "python3", args: ["../reporting/generate_report.py"] },
];

interface RunConfig {
  backupPath: string;
  resultsPath?: string;
  dbUrl: string;
}

/**
 * Derives <workspace>/results/<name>/ from <workspace>/decrypted/<name>/
 * by swapping the one path segment mvt-runner's fixed layout guarantees
 * differs between the two. Mirrors extractors/mvt_iocs/main.py's own
 * fallback logic exactly, so the two stay in sync — this is best-effort
 * plumbing, not validation; a stage that actually needs the directory to
 * exist checks that itself.
 */
function deriveResultsPath(backupPath: string): string | undefined {
  const parts = backupPath.split(path.sep);
  const idx = parts.indexOf("decrypted");
  if (idx === -1) return undefined;
  parts[idx] = "results";
  return parts.join(path.sep);
}

/**
 * True if `backupPath` already has a pipeline_runs row that both finished
 * and had zero failed stages. Stage-level failures deliberately do NOT
 * count as "succeeded" here — a fixed extractor should get a chance to
 * fill in a previously-failed stage on re-run, so only a clean run is
 * skippable. This is what keeps a --workspace re-run cheap once a backlog
 * of backups has mostly been processed, without silently leaving gaps.
 */
async function hasSucceededRun(client: Client, backupPath: string): Promise<boolean> {
  const { rows } = await client.query(
    `SELECT pr.run_id
     FROM pipeline_runs pr
     WHERE pr.backup_source = $1
       AND pr.finished_at IS NOT NULL
       AND NOT EXISTS (
         SELECT 1 FROM pipeline_stage_status pss
         WHERE pss.run_id = pr.run_id AND pss.status = 'failed'
       )
     LIMIT 1`,
    [backupPath]
  );
  return rows.length > 0;
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
    const extraArgs = ["--run-id", runId, "--backup-path", config.backupPath, "--db-url", config.dbUrl];
    if (config.resultsPath) {
      extraArgs.push("--results-path", config.resultsPath);
    }
    const child = spawn(stage.command, [...stage.args, ...extraArgs], {
      stdio: ["ignore", "pipe", "pipe"],
    });

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

interface CliConfig {
  backupPaths: string[];
  dbUrl: string;
}

function printUsage() {
  console.error(`Usage:
  main.ts --workspace <mvt-runner-workspace-dir>
      Discovers every backup already decrypted by mvt-runner under
      <workspace>/decrypted/*, and runs the full pipeline against each.

  main.ts <path-to-decrypted-backup> [<path> ...]
      Runs the full pipeline against one or more explicit decrypted-backup
      directories (bypassing mvt-runner's workspace convention).`);
}

async function parseCliConfig(): Promise<CliConfig> {
  const { values, positionals } = parseArgs({
    args: process.argv.slice(2),
    options: {
      workspace: { type: "string" },
    },
    allowPositionals: true,
  });

  const dbUrl = process.env.DATABASE_URL ?? "postgresql://localhost:5432/forensics";

  if (values.workspace) {
    const decryptedDir = path.join(values.workspace, "decrypted");
    let entries;
    try {
      entries = await fsp.readdir(decryptedDir, { withFileTypes: true });
    } catch (err) {
      console.error(
        `[orchestrator] could not read ${decryptedDir}: ${err instanceof Error ? err.message : err}`
      );
      console.error(`[orchestrator] has mvt-runner been run against this workspace yet?`);
      process.exit(1);
    }
    // Only queue backups mvt-runner actually finished decrypting. repair/check
    // have their own separate markers and are best-effort — decrypt succeeding
    // is the one precondition this pipeline actually needs.
    const candidates = entries.filter((e) => e.isDirectory());
    const backupPaths: string[] = [];
    const skippedIncomplete: string[] = [];
    for (const entry of candidates) {
      const dir = path.join(decryptedDir, entry.name);
      const markerExists = await fsp
        .access(path.join(dir, ".mvt_decrypted_ok"))
        .then(() => true)
        .catch(() => false);
      if (markerExists) {
        backupPaths.push(dir);
      } else {
        skippedIncomplete.push(dir);
      }
    }
    backupPaths.sort();
    if (skippedIncomplete.length > 0) {
      console.log(`[orchestrator] skipping ${skippedIncomplete.length} incomplete decrypt(s) (no .mvt_decrypted_ok):`);
      for (const dir of skippedIncomplete) console.log(`  - ${dir}`);
    }
    if (backupPaths.length === 0) {
      console.error(`[orchestrator] no fully-decrypted backups found under ${decryptedDir}`);
      process.exit(1);
    }
    return { backupPaths, dbUrl };
  }

  if (positionals.length === 0) {
    printUsage();
    process.exit(1);
  }
  return { backupPaths: positionals, dbUrl };
}

/**
 * Runs the full stage pipeline against a single backup. Never throws —
 * a backup-level failure (e.g. Postgres unreachable mid-run) is caught by
 * the caller's per-backup try/catch in main(), so one bad backup can't
 * take down the ones after it in the same invocation.
 */
async function runPipelineForBackup(
  client: Client,
  backupPath: string,
  dbUrl: string
): Promise<{ runId: string; results: { stage: string; success: boolean }[] }> {
  const runId = await createRun(client, backupPath);
  const resultsPath = deriveResultsPath(backupPath);
  console.log(`[orchestrator] run ${runId} started against ${backupPath}`);
  if (resultsPath) {
    console.log(`[orchestrator]   (results dir: ${resultsPath})`);
  }

  const results: { stage: string; success: boolean }[] = [];

  for (const stage of STAGES) {
    console.log(`[orchestrator] -> ${stage.name}`);
    await markStage(client, runId, stage.name, "running");

    const { success, stderr } = await runStage(stage, { backupPath, resultsPath, dbUrl }, runId);

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
  return { runId, results };
}

async function main() {
  const cfg = await parseCliConfig();

  const dbUrl = cfg.dbUrl;
  const client = new Client({ connectionString: dbUrl });
  await client.connect();

  console.log(`[orchestrator] processing ${cfg.backupPaths.length} backup(s)`);

  const summary: { backupPath: string; runId?: string; failedStages: string[]; error?: string; skipped?: boolean }[] = [];

  for (const backupPath of cfg.backupPaths) {
    if (await hasSucceededRun(client, backupPath)) {
      console.log(`\n[orchestrator] ===== ${backupPath} ===== (skipped — already fully succeeded)`);
      summary.push({ backupPath, failedStages: [], skipped: true });
      continue;
    }
    console.log(`\n[orchestrator] ===== ${backupPath} =====`);
    try {
      const { runId, results } = await runPipelineForBackup(client, backupPath, dbUrl);
      const failedStages = results.filter((r) => !r.success).map((r) => r.stage);
      summary.push({ backupPath, runId, failedStages });
    } catch (err) {
      // A failure here means something broke outside per-stage handling
      // (e.g. couldn't even create the pipeline_run row) — log it against
      // this backup and move on to the next one rather than aborting the
      // whole multi-backup invocation.
      const message = err instanceof Error ? err.message : String(err);
      console.error(`[orchestrator] backup-level failure for ${backupPath}: ${message}`);
      summary.push({ backupPath, failedStages: [], error: message });
    }
  }

  await client.end();

  console.log("\n[orchestrator] all backups processed");
  for (const s of summary) {
    if (s.skipped) {
      console.log(`  ${s.backupPath}: skipped — already fully succeeded`);
    } else if (s.error) {
      console.log(`  ${s.backupPath}: FAILED before stages ran — ${s.error}`);
    } else if (s.failedStages.length === 0) {
      console.log(`  ${s.backupPath}: run ${s.runId} — all stages succeeded`);
    } else {
      console.log(`  ${s.backupPath}: run ${s.runId} — failed stages: ${s.failedStages.join(", ")}`);
    }
  }

  const anyFailed = summary.some((s) => s.error || s.failedStages.length > 0);
  if (anyFailed) {
    console.log(`\n  -> fix and re-run against the same workspace/backups to fill in gaps`);
    console.log(`     (idempotent — already-succeeded stages will not be redone).`);
  }
}

main().catch((err) => {
  // This top-level catch is a last resort — it should only ever fire for
  // infrastructure problems (e.g. can't reach Postgres at all), never for
  // a single extractor's failure, which is handled per-stage above.
  console.error("[orchestrator] fatal error outside stage handling:", err);
  process.exit(1);
});
