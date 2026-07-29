import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

const outputRoot = new URL("../pages-dist/", import.meta.url);

test("builds a public GitHub Pages entry point", async () => {
  const html = await readFile(new URL("index.html", outputRoot), "utf8");

  assert.match(html, /<title>GuardianSim: Parallel Futures<\/title>/i);
  assert.match(html, /nvm-star-max\.github\.io\/GuardianSim/);
  assert.match(html, /og-parallel-futures\.png/);
  assert.match(html, /assets\/[^"]+\.js/);
  assert.match(html, /assets\/[^"]+\.css/);
  assert.doesNotMatch(html, /signin-with-chatgpt|codex-preview/i);
});

test("copies immutable showcase media into the static build", async () => {
  await access(new URL("seed-411-parallel-futures.mp4", outputRoot));
  await access(new URL("seed-411-preview.png", outputRoot));
  await access(new URL("og-parallel-futures.png", outputRoot));
  await access(new URL("favicon.svg", outputRoot));
});
