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
    /<title>GuardianSim · Auditable safety for Physical AI<\/title>/i,
  );
  assert.match(html, /Choose safer\./);
  assert.match(html, /Prove it\./);
  assert.match(html, /30\/30/);
  assert.match(html, /\+98\.36%/);
  assert.match(html, /30 to 0 clutter contacts/);
  assert.match(html, /Failure became protocol/);
  assert.match(html, /No physical-robot deployment claim/);
  assert.doesNotMatch(html, /codex-preview|react-loading-skeleton/i);
});

test("ships audit links and finished site metadata", async () => {
  const [page, client, layout, packageJson] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/ShowcaseClient.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
  ]);

  assert.match(page, /<ShowcaseClient \/>/);
  assert.match(client, /formal-report\.json/);
  assert.match(client, /Gate 3\.2 evidence frozen/);
  assert.match(client, /90s presenter mode/);
  assert.match(layout, /summary_large_image/);
  assert.match(layout, /\/og\.png/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);

  await access(new URL("../public/og.png", import.meta.url));
});
