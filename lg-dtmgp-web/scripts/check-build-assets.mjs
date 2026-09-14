import { access, readFile } from "node:fs/promises";
import { resolve } from "node:path";

const distDirectory = resolve("dist");
const html = await readFile(resolve(distDirectory, "index.html"), "utf8");
const references = [...html.matchAll(/(?:src|href)="([^"?#]+)"/g)]
  .map((match) => match[1])
  .filter((reference) => reference.startsWith("/assets/"));

if (references.length === 0) {
  throw new Error("dist/index.html does not reference any hashed assets");
}

for (const reference of references) {
  await access(resolve(distDirectory, reference.slice(1)));
  if (!/-[A-Za-z0-9_-]{8,}\.(?:css|js)$/.test(reference)) {
    throw new Error(`Asset is not content-hashed: ${reference}`);
  }
}

await access(resolve(distDirectory, "runtime-config.json"));
await access(resolve(distDirectory, "benue-govt-logo.jpeg"));
console.log(`Verified ${references.length} hashed assets and runtime files.`);
