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

test("ships visible measurements before gate evaluation", async () => {
  const html = await readFile(new URL("index.html", outputRoot), "utf8");
  const scriptPath = html.match(/src="([^"]+\.js)"/)?.[1];

  assert.ok(scriptPath, "static JavaScript bundle is missing");
  const scriptName = scriptPath.split("/").at(-1);
  assert.ok(scriptName, "static JavaScript bundle name is missing");

  const script = await readFile(
    new URL(`assets/${scriptName}`, outputRoot),
    "utf8",
  );
  assert.match(script, /Verified measurements loaded/);
  assert.match(script, /APPLY GATES TO 18 FUTURES/);
  assert.match(script, /−1\.42 mm/);
  assert.match(script, /0\.936/);
});
