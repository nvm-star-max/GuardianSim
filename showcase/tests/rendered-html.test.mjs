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

test("server-renders the GuardianSim Parallel Futures arena", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(
    html,
    /<title>GuardianSim: Parallel Futures<\/title>/i,
  );
  assert.match(html, /See three futures/);
  assert.match(html, /Try to break GuardianSim/);
  assert.match(html, /RUN 18 FUTURES/);
  assert.match(html, /Seed 411/);
  assert.match(html, /Seed 509/);
  assert.match(html, /30\/30/);
  assert.match(html, /\+98\.36%/);
  assert.match(html, /No physical-robot deployment claim/i);
  assert.doesNotMatch(html, /codex-preview|react-loading-skeleton/i);
});

test("ships immutable audit links, replay assets, and finished metadata", async () => {
  const [page, client, layout, packageJson] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/ShowcaseClient.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
  ]);

  assert.match(page, /<ShowcaseClient \/>/);
  assert.match(client, /formal-report\.json/);
  assert.match(client, /unsafe_nominal_replaced/);
  assert.match(client, /higher_margin_alternative/);
  assert.match(client, /safe_stop/);
  assert.match(client, /downloadReceipt/);
  assert.match(client, /seed-411-parallel-futures\.mp4/);
  assert.match(layout, /summary_large_image/);
  assert.match(layout, /\/og-parallel-futures\.png/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);

  await access(
    new URL("../public/og-parallel-futures.png", import.meta.url),
  );
  await access(
    new URL("../public/seed-411-parallel-futures.mp4", import.meta.url),
  );
  await access(new URL("../public/seed-411-preview.png", import.meta.url));
});

test("interactive claims match the preserved Gate 3.2 and Gate 3.3 reports", async () => {
  const [client, gate32Text, gate33Text] = await Promise.all([
    readFile(new URL("../app/ShowcaseClient.tsx", import.meta.url), "utf8"),
    readFile(
      new URL(
        "../../docs/evidence/gate-3-2/formal-report.json",
        import.meta.url,
      ),
      "utf8",
    ),
    readFile(
      new URL(
        "../../docs/evidence/gate-3-3-two-strata/raw/two-strata-report.json",
        import.meta.url,
      ),
      "utf8",
    ),
  ]);

  const gate32 = JSON.parse(gate32Text);
  const gate33 = JSON.parse(gate33Text);
  const seed411 = gate32.episodes.find((episode) => episode.seed === 411);
  const seed401 = gate32.episodes.find((episode) => episode.seed === 401);
  const seed509 = gate33.episodes.find((episode) => episode.seed === 509);

  assert.equal(gate32.completed_episode_count, 30);
  assert.equal(gate32.summary.baseline.repeatable_safe_completion_count, 18);
  assert.equal(
    gate32.summary.guardiansim.repeatable_safe_completion_count,
    30,
  );
  assert.equal(gate32.summary.baseline.execution_safe_completion_count, 58);
  assert.equal(gate32.summary.guardiansim.execution_safe_completion_count, 90);
  assert.equal(gate32.summary.baseline.clutter_contact_count, 30);
  assert.equal(gate32.summary.guardiansim.clutter_contact_count, 0);

  assert.equal(seed411.selection.decision, "unsafe_nominal_replaced");
  assert.equal(
    seed411.guardiansim.candidate.candidate_id,
    "yaw_+67.5_retreat_+0.000_approach_+0.140",
  );
  assert.equal(seed401.selection.decision, "higher_margin_alternative");
  assert.equal(seed509.selection.decision, "safe_stop");
  assert.equal(seed509.guardiansim.safe_stopped, true);

  assert.match(client, /1\.42 mm/);
  assert.match(client, /17\.1 mm/);
  assert.match(client, /59\.4 mm/);
  assert.match(client, /98\.4 mm/);
  assert.match(client, /8\.29 mm/);
  assert.match(client, /28\.6 mm/);
});
