/**
 * FastAPI(8000) 없이 Streamlit과 동일 SQLite/KV에서 브리핑 로드.
 */
import { execFile } from "node:child_process";
import path from "node:path";
import { promisify } from "node:util";

import type { SajuBriefing } from "@/types/saju-briefing";

const execFileAsync = promisify(execFile);

function repoRoot(): string {
  return path.resolve(process.cwd(), "..");
}

function pythonExecutable(): string {
  return process.env.SAJU_PYTHON?.trim() || "python";
}

export async function loadBriefingFromLocalProject(
  fingerprint: string
): Promise<SajuBriefing | null> {
  const fp = String(fingerprint || "").trim();
  if (!fp) return null;

  const root = repoRoot();
  const script = path.join(root, "scripts", "briefing_get_json.py");

  try {
    const { stdout } = await execFileAsync(
      pythonExecutable(),
      [script, fp],
      {
        cwd: root,
        timeout: 20_000,
        maxBuffer: 12 * 1024 * 1024,
        windowsHide: true,
      }
    );
    const raw = String(stdout || "").trim();
    if (!raw || raw === "null") return null;
    const parsed = JSON.parse(raw) as SajuBriefing;
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch {
    return null;
  }
}
