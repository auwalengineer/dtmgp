import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

function gitCommit() {
  if (process.env.GITHUB_SHA) return process.env.GITHUB_SHA;
  try {
    const gitDirectory = resolve("..", ".git");
    const head = readFileSync(resolve(gitDirectory, "HEAD"), "utf8").trim();
    if (!head.startsWith("ref: ")) return head;
    return readFileSync(resolve(gitDirectory, head.slice(5)), "utf8").trim();
  }
  catch { return "development"; }
}

const metadata = {
  version: process.env.npm_package_version || "0.0.0",
  commit: gitCommit(),
  build_time: new Date().toISOString(),
};
mkdirSync("public", { recursive: true });
writeFileSync("public/version.json", `${JSON.stringify(metadata, null, 2)}\n`);
