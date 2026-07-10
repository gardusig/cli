#!/usr/bin/env node
/**
 * Validate ```mermaid fences under system-design/.
 *
 * 1. Syntax — @mermaid-js/mermaid-cli (mmdc) with puppeteer.config.cjs for CI.
 * 2. Design — examples/** flowchart TB blocks must include the architecture palette
 *    from patterns/architecture-diagram-conventions.md.
 */

import { execFile } from "node:child_process";
import { mkdtemp, readdir, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, relative, resolve } from "node:path";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";

const execFileAsync = promisify(execFile);
const __dirname = fileURLToPath(new URL(".", import.meta.url));
const SYSTEM_DESIGN_ROOT = resolve(
  process.env.SYSTEM_DESIGN_ROOT || "/workspace/interviewing/system-design",
);
const MMDC = resolve(__dirname, "node_modules", ".bin", "mmdc");
const PUPPETEER_CONFIG = resolve(__dirname, "puppeteer.config.json");

/** Intentional partial / invalid samples — syntax check skipped. */
const SYNTAX_LINT_SKIP = new Set(["patterns/example-authoring-template.md"]);

const DESIGN_LINT_SKIP = new Set([
  "README.md",
  "patterns/example-authoring-template.md",
  "patterns/event-driven-architecture.md",
  "patterns/aws-reference-layout.md",
  "patterns/aws-service-drill-template.md",
  "patterns/architecture-diagram-conventions.md",
]);

const ARCHITECTURE_PALETTE = [
  { name: "user", fill: "#e3f2fd" },
  { name: "edge", fill: "#fff3e0" },
  { name: "app", fill: "#e8f5e9" },
  { name: "data", fill: "#fce4ec" },
  { name: "async", fill: "#f3e5f5" },
];

const MERMAID_BLOCK_RE = /^```mermaid\s*\r?\n([\s\S]*?)\r?\n```/gm;

async function walkMarkdownFiles(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "scripts" || entry.name === "node_modules") continue;
      files.push(...(await walkMarkdownFiles(full)));
    } else if (entry.isFile() && entry.name.endsWith(".md")) {
      files.push(full);
    }
  }
  return files.sort();
}

function extractMermaidBlocks(content) {
  const blocks = [];
  let match;
  while ((match = MERMAID_BLOCK_RE.exec(content)) !== null) {
    const code = match[1].trimEnd();
    const startLine =
      content.slice(0, match.index).split(/\r?\n/).length;
    blocks.push({ code, startLine });
  }
  return blocks;
}

async function validateSyntax(code) {
  const dir = await mkdtemp(join(tmpdir(), "mermaid-val-"));
  const input = join(dir, "diagram.mmd");
  const output = join(dir, "diagram.svg");
  await writeFile(input, `${code}\n`, "utf8");
  try {
    await execFileAsync(
      MMDC,
      [
        "-i",
        input,
        "-o",
        output,
        "-q",
        "--backgroundColor",
        "transparent",
        "-p",
        PUPPETEER_CONFIG,
      ],
      { env: process.env, maxBuffer: 10 * 1024 * 1024 },
    );
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
}

function shouldDesignLint(relPath) {
  if (DESIGN_LINT_SKIP.has(relPath)) return false;
  return relPath.startsWith("examples/");
}

function lintArchitecturePalette(relPath, code, startLine) {
  const issues = [];
  if (!shouldDesignLint(relPath)) return issues;

  if (!/\bflowchart\s+tb\b/i.test(code)) return issues;

  for (const { name, fill } of ARCHITECTURE_PALETTE) {
    const re = new RegExp(
      `classdef\\s+${name}\\b[^\\n]*fill:\\s*${fill}`,
      "i",
    );
    if (!re.test(code)) {
      issues.push(
        `missing or wrong classDef ${name} (expected fill:${fill}) — see patterns/architecture-diagram-conventions.md`,
      );
    }
  }

  if (!/\bclass\s+[\w,]+\s+(user|edge|app|data|async)\b/i.test(code)) {
    issues.push(
      "flowchart TB has palette classDefs but no `class <nodes> <role>` assignments",
    );
  }

  return issues.map((message) => ({ line: startLine, message }));
}

function firstLine(stderrOrStdout) {
  const text = (stderrOrStdout ?? "").trim();
  if (!text) return "mmdc failed";
  const line = text.split("\n").find((l) => l.trim()) ?? text;
  if (line.includes("Failed to launch the browser")) {
    return "Failed to launch Chromium (CI: ensure puppeteer browsers install step runs)";
  }
  return line;
}

async function main() {
  const files = await walkMarkdownFiles(SYSTEM_DESIGN_ROOT);
  let blockCount = 0;
  let filesWithDiagrams = 0;
  const errors = [];

  for (const filePath of files) {
    const relPath = relative(SYSTEM_DESIGN_ROOT, filePath);
    const content = await readFile(filePath, "utf8");
    const blocks = extractMermaidBlocks(content);
    if (blocks.length === 0) continue;
    filesWithDiagrams += 1;
    const skipSyntax = SYNTAX_LINT_SKIP.has(relPath);

    for (const { code, startLine } of blocks) {
      blockCount += 1;
      const label = `${relPath}:${startLine}`;

      if (!skipSyntax) {
        try {
          await validateSyntax(code);
        } catch (err) {
          const detail =
            firstLine(err.stderr) ||
            firstLine(err.stdout) ||
            err?.message ||
            String(err);
          errors.push(`${label}: syntax — ${detail}`);
          continue;
        }
      }

      for (const { line, message } of lintArchitecturePalette(
        relPath,
        code,
        startLine,
      )) {
        errors.push(`${relPath}:${line}: design — ${message}`);
      }
    }
  }

  if (errors.length > 0) {
    console.error(`Mermaid validation failed (${errors.length} issue(s)):\n`);
    for (const e of errors) console.error(`  • ${e}`);
    process.exit(1);
  }

  console.log(
    `OK — ${blockCount} diagram(s) in ${filesWithDiagrams} file(s) (${files.length} markdown files scanned)`,
  );
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
