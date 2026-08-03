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
  assert.match(html, /Think thousands/);
  assert.match(html, /Execute one/);
  assert.match(html, /PARALLEL FUTURE ENGINE/);
  assert.match(html, /16,384/);
  assert.match(html, /293\.6M/);
  assert.match(html, /278,051/);
  assert.match(html, /98\.33%/);
  assert.match(html, /Thousands of measured futures\. One decision\./);
  assert.match(html, /4,608/);
  assert.match(html, /MEASURED WITH ROCM/);
  assert.match(html, /Try to break GuardianSim/);
  assert.match(html, /APPLY GATES TO 18 FUTURES/);
  assert.match(html, /Seed 411/);
  assert.match(html, /Seed 509/);
  assert.match(html, /1,387/);
  assert.match(html, /1,185/);
  assert.match(html, /202/);
  assert.match(html, /30\/30/);
  assert.match(html, /\+98\.36%/);
  assert.match(html, /No physical-robot deployment claim/i);
  assert.match(html, /One Radeon GPU\. 16,384 robot worlds\./);
  assert.match(html, /167,772,160 measured environment steps/);
  assert.match(html, /278,051 env-steps\/s/);
  assert.match(html, /1\.82×/);
  assert.match(html, /98\.82% batch mean · 100% peak/);
  assert.match(html, /22\.05 GiB/);
  assert.match(html, /15 independent-process measurements/);
  assert.match(html, /18 actions\. 256 uncertain worlds each\./);
  assert.match(html, /4,608/);
  assert.match(html, /candidates passed 256\/256/);
  assert.match(html, /10,143\.979/);
  assert.match(html, /2,299,392/);
  assert.match(html, /73\.406% mean · 97% peak/);
  assert.match(html, /1,691/);
  assert.match(html, /not 4,608 independent robot trials/);
  assert.match(html, /STRICT SCHEMA-3 VALIDATION PASSED/);
  assert.doesNotMatch(html, /pending strict validation/i);
  assert.match(html, /not training\s+examples or independent safety trials/);
  assert.doesNotMatch(html, /One GPU\. 256 robot worlds\./);
  assert.doesNotMatch(html, /337,000 measured environment steps/);
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
  assert.match(client, /SafetySwarmHeatmap/);
  assert.match(client, /975a82b3e09d0458a4c02ac945859f2fdf874c4f/);
  assert.match(layout, /card: "summary"/);
  assert.doesNotMatch(layout, /\/og-parallel-futures\.png/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);

  await access(
    new URL("../public/seed-411-parallel-futures.mp4", import.meta.url),
  );
  await access(new URL("../public/seed-411-preview.png", import.meta.url));
});

test("Safety Swarm showcase data is generated from the preserved formal report", async () => {
  const [generatedSource, reportText] = await Promise.all([
    readFile(
      new URL("../app/safetySwarmFormal.generated.ts", import.meta.url),
      "utf8",
    ),
    readFile(
      new URL(
        "../../docs/evidence/safety-swarm-v2-formal-2026-07-30/formal-report.json",
        import.meta.url,
      ),
      "utf8",
    ),
  ]);

  const formalMatch = generatedSource.match(
    /export const safetySwarmFormal = ([\s\S]*?) as const;/,
  );
  const rowsMatch = generatedSource.match(
    /export const safetySwarmRows = ([\s\S]*?) as const;/,
  );
  assert.ok(formalMatch, "generated formal summary is missing");
  assert.ok(rowsMatch, "generated heatmap rows are missing");

  const generated = JSON.parse(formalMatch[1]);
  const rows = JSON.parse(rowsMatch[1]);
  const report = JSON.parse(reportText);

  assert.equal(generated.reportSha256, report.report_sha256);
  assert.equal(generated.candidateWorldCount, 4608);
  assert.equal(generated.candidateCount, 18);
  assert.equal(generated.worldCountPerCandidate, 256);
  assert.equal(generated.qualifyingCandidateCount, 5);
  assert.equal(generated.totalEnvironmentSteps, 2299392);
  assert.equal(generated.maxGpuUtilizationPct, 97);

  assert.equal(rows.length, 18);
  assert.equal(rows.filter((row) => row.qualifies).length, 5);
  assert.equal(rows.filter((row) => row.selected).length, 1);
  assert.ok(rows.every((row) => row.outcomes.length === 256));
  assert.equal(
    rows.reduce(
      (total, row) =>
        total + Array.from(row.outcomes).filter((code) => code === "S").length,
      0,
    ),
    report.summary.safe_candidate_world_count,
  );
  assert.equal(
    rows.reduce(
      (total, row) =>
        total + Array.from(row.outcomes).filter((code) => code === "C").length,
      0,
    ),
    report.summary.contact_candidate_world_count,
  );
});

test("Radeon Scale V3 claims match the preserved schema-3 report", async () => {
  const [client, reportText] = await Promise.all([
    readFile(new URL("../app/ShowcaseClient.tsx", import.meta.url), "utf8"),
    readFile(
      new URL(
        "../../docs/evidence/radeon-scale-v3-formal-2026-08-03/report.json",
        import.meta.url,
      ),
      "utf8",
    ),
  ]);

  const report = JSON.parse(reportText);
  const largest = report.batch_summaries.find((batch) => batch.n_envs === 16384);

  assert.equal(report.schema_version, 3);
  assert.equal(report.summary.measurement_count, 15);
  assert.equal(report.summary.largest_parallel_batch, 16384);
  assert.equal(report.summary.total_measured_environment_steps, 293601280);
  assert.equal(report.summary.peak_gpu_utilization_pct, 100);
  assert.equal(largest.repeat_count, 5);
  assert.equal(largest.peak_vram_used_bytes, 23677100032);
  assert.ok(
    Math.abs(largest.throughput_p50 - 278051.243641299) <
      1e-9,
  );
  assert.ok(
    Math.abs(
      report.summary.largest_vs_smallest_batch_p50_ratio -
        1.8209299806018995,
    ) < 1e-9,
  );

  assert.match(client, /278,051/);
  assert.match(client, /1\.82×/);
  assert.match(client, /293\.6M/);
  assert.match(client, /22\.05 GiB/);
  assert.match(client, /STRICT SCHEMA-3 VALIDATION PASSED/);
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

  const countGate32 = gate32.episodes.reduce(
    (counts, episode) => {
      counts.rollouts += Object.keys(
        episode.selection.initial_metrics_by_id,
      ).length;
      counts.rollouts += Object.values(
        episode.selection.observations_by_id,
      ).reduce((total, observations) => total + observations.length - 1, 0);
      counts.executions += episode.baseline.executions.length;
      counts.executions += episode.guardiansim.executions.length;
      return counts;
    },
    { rollouts: 0, executions: 0 },
  );
  const countGate33 = gate33.episodes.reduce(
    (counts, episode) => {
      counts.rollouts += Object.keys(
        episode.selection.initial_raw_metrics_by_id,
      ).length;
      counts.rollouts += Object.values(
        episode.selection.observations_by_id,
      ).reduce((total, observations) => total + observations.length - 1, 0);
      counts.executions += Number(episode.baseline.execution !== null);
      counts.executions += Number(episode.guardiansim.execution !== null);
      return counts;
    },
    { rollouts: 0, executions: 0 },
  );

  assert.equal(gate32.episodes.length + gate33.episodes.length, 42);
  assert.equal(countGate32.rollouts + countGate33.rollouts, 1185);
  assert.equal(countGate32.executions + countGate33.executions, 202);
  assert.equal(
    countGate32.rollouts
      + countGate33.rollouts
      + countGate32.executions
      + countGate33.executions,
    1387,
  );
  assert.match(client, /1,387/);
  assert.match(client, /1,185/);
  assert.match(client, /202/);

  assert.match(client, /1\.42 mm/);
  assert.match(client, /17\.1 mm/);
  assert.match(client, /59\.4 mm/);
  assert.match(client, /98\.4 mm/);
  assert.match(client, /8\.29 mm/);
  assert.match(client, /28\.6 mm/);
  assert.match(client, /CLEARANCE <b>{future\.clearance}<\/b>/);
  assert.match(client, /STABILITY <b>{future\.stability}<\/b>/);
  assert.doesNotMatch(client, /future\.clearance : "—"/);
  assert.doesNotMatch(client, /future\.stability : "—"/);
});
