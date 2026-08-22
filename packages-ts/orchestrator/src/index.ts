import { spawn } from 'child_process';
import { randomUUID } from 'crypto';
import * as path from 'path';
import * as fs from 'fs';

export interface IngestionJobOptions {
  inputPath: string;
  outputPath?: string;
  dbPath?: string;
  cleanStaging?: boolean;
}

export interface IngestionResult {
  success: boolean;
  exitCode: number | null;
  logs: string;
  error?: string;
}

export class IngestionOrchestrator {
  private workspaceRoot: PathLike;

  constructor(workspaceRoot?: string) {
    // Resolve monorepo root dynamically or fallback relative to package location
    this.workspaceRoot = workspaceRoot || path.resolve(__dirname, '../../..');
  }

  /**
   * Spawns the Python iLEAPP end-to-end ingestion pipeline safely.
   */
  public async runIngestionPipeline(
    options: IngestionJobOptions,
    onLog?: (data: string) => void
  ): Promise<IngestionResult> {
    const pythonExecutable = path.join(this.workspaceRoot as string, '.venv', 'bin', 'python');
    const pipelineScript = path.join(
      this.workspaceRoot as string,
      'packages-py',
      'extractors',
      'ileapp_bridge',
      'main.py'
    );

    // Validate environment prerequisites
    if (!fs.existsSync(pythonExecutable)) {
      throw new Error(`Python virtual environment interpreter not found at: ${pythonExecutable}`);
    }
    if (!fs.existsSync(pipelineScript)) {
      throw new Error(`Python pipeline script not found at: ${pipelineScript}`);
    }

    const outputPath = options.outputPath || path.join(this.workspaceRoot as string, 'ileapp_raw_output');
    const dbUrl = process.env.DATABASE_URL ?? 'postgresql://localhost:5432/forensics';
    const runId = randomUUID();

    const args = [
      pipelineScript,
      '--run-id', runId,
      '--backup-path', options.inputPath,
      '--db-url', options.dbPath || dbUrl,
      '--output', outputPath
    ];

    if (options.cleanStaging) {
      args.push('--clean');
    }

    return new Promise((resolve) => {
      let stdoutLogs = '';
      let stderrLogs = '';

      console.log(`[*] Spawning Python pipeline: ${pythonExecutable} ${args.join(' ')}`);
      
      const child = spawn(pythonExecutable, args);

      child.stdout.on('data', (data) => {
        const text = data.toString();
        stdoutLogs += text;
        if (onLog) onLog(text);
      });

      child.stderr.on('data', (data) => {
        const text = data.toString();
        stderrLogs += text;
        if (onLog) onLog(`[ERROR] ${text}`);
      });

      child.on('close', (code) => {
        const success = code === 0;
        resolve({
          success,
          exitCode: code,
          logs: stdoutLogs,
          error: success ? undefined : stderrLogs || `Process exited with code ${code}`
        });
      });

      child.on('error', (err) => {
        resolve({
          success: false,
          exitCode: -1,
          logs: stdoutLogs,
          error: err.message
        });
      });
    });
  }
}

type PathLike = string;