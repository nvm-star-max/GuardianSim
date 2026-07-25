import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("server-renders the GuardianSim evidence story", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(
    html,
    /<title>GuardianSim · Repeatability-aware Physical AI<\/title>/i,
  );
  assert.match(html, /Simulate twice\./);
  assert.match(html, /Fail safely\./);
  assert.match(html, /20\/20/);
  assert.match(html, /\+63\.93%/);
  assert.match(html, /240/);
  assert.match(html, /Gate 2\.7 is not hidden/);
  assert.match(html, /No physical-robot deployment claim/);
  assert.doesNotMatch(html, /codex-preview|react-loading-skeleton/i);
});

test("ships audit evidence and finished site metadata", async () => {
  const [page, client, layout, packageJson, report] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/ShowcaseClient.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
    readFile(
      new URL("../public/evidence/gate-2-8-report.json", import.meta.url),
      "utf8",
    ),
  ]);

  assert.match(page, /<ShowcaseClient \/>/);
  assert.match(client, /gate-2-8-report\.json/);
  assert.match(client, /90s presenter mode/);
  assert.match(layout, /summary_large_image/);
  assert.match(layout, /\/og\.png/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);

  const evidence = JSON.parse(report);
  assert.equal(evidence.schema_version, 3);
  assert.equal(evidence.completed_episode_count, 20);
  assert.equal(evidence.summary.guardiansim.success_count, 20);

  await access(new URL("../public/og.png", import.meta.url));
  await access(
    new URL("../public/evidence/gate-2-8-terminal.png", import.meta.url),
  );
});
