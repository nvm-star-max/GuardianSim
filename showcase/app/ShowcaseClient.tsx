"use client";

import { useMemo, useState } from "react";

type ChallengeKey = "collision" | "margin" | "stop";
type Phase = "idle" | "running" | "revealed";
type Tone = "danger" | "warning" | "safe";

type Future = {
  id: string;
  label: string;
  action: string;
  clearance: string;
  stability: string;
  verdict: string;
  reason: string;
  tone: Tone;
  trajectory: "straight" | "left" | "right";
};

type Challenge = {
  eyebrow: string;
  seed: number;
  title: string;
  prompt: string;
  scene: string;
  protocol: string;
  sourceLabel: string;
  sourceUrl: string;
  reportHash: string;
  fingerprint: string;
  decision: string;
  outcome: string;
  outcomeDetail: string;
  outcomeTone: Tone;
  futures: Future[];
};

const GATE_32_REPORT =
  "https://github.com/nvm-star-max/GuardianSim/blob/25e27aced13237b5af93fd91697d7abb12101a30/docs/evidence/gate-3-2/formal-report.json";
const GATE_33_REPORT =
  "https://github.com/nvm-star-max/GuardianSim/blob/25e27aced13237b5af93fd91697d7abb12101a30/docs/evidence/gate-3-3-two-strata/raw/two-strata-report.json";

const challenges: Record<ChallengeKey, Challenge> = {
  collision: {
    eyebrow: "COLLISION TRAP · FORMAL GATE 3.2",
    seed: 411,
    title: "The obvious grasp clips the plum.",
    prompt:
      "Pick the lemon without touching nearby clutter. Which future should the robot execute?",
    scene: "Lemon pick · lateral plum clutter · unseen seed 411",
    protocol: "Schema 5 · frozen 30-scenario protocol · 3 repeats",
    sourceLabel: "Inspect Seed 411 in the frozen report",
    sourceUrl: GATE_32_REPORT,
    reportHash:
      "d76ffbe518d4cb9499362379388a1453ec6cc7614ff312b9bcf764dbf822ffee",
    fingerprint:
      "7b43207acd291f2db19a5fc3c4cabdd88e297c0d2c48307b6d35a4659fa047e7",
    decision: "unsafe_nominal_replaced",
    outcome: "Future C selected",
    outcomeDetail:
      "The nominal path overlapped clutter in all 3 executions. The +67.5° approach preserved 17.1 mm clearance and completed safely 3/3 times.",
    outcomeTone: "safe",
    futures: [
      {
        id: "A",
        label: "Nominal",
        action: "Yaw 0° · direct approach",
        clearance: "−1.42 mm",
        stability: "0.936",
        verdict: "COLLISION",
        reason: "Physical overlap with plum",
        tone: "danger",
        trajectory: "straight",
      },
      {
        id: "B",
        label: "Wide retreat",
        action: "Yaw +90° · retreat 25 mm",
        clearance: "59.4 mm",
        stability: "0.000",
        verdict: "REJECTED",
        reason: "Clear, but unstable lift",
        tone: "warning",
        trajectory: "right",
      },
      {
        id: "C",
        label: "Guardian choice",
        action: "Yaw +67.5° · approach 140 mm",
        clearance: "17.1 mm",
        stability: "0.948",
        verdict: "SELECTED",
        reason: "All hard gates passed",
        tone: "safe",
        trajectory: "left",
      },
    ],
  },
  margin: {
    eyebrow: "MARGIN BOOST · FORMAL GATE 3.2",
    seed: 401,
    title: "Safe is not the same as safest.",
    prompt:
      "The nominal grasp is already safe. Can GuardianSim find a more robust future without sacrificing stability?",
    scene: "Banana pick · lateral clutter · unseen seed 401",
    protocol: "Schema 5 · frozen 30-scenario protocol · 3 repeats",
    sourceLabel: "Inspect Seed 401 in the frozen report",
    sourceUrl: GATE_32_REPORT,
    reportHash:
      "d76ffbe518d4cb9499362379388a1453ec6cc7614ff312b9bcf764dbf822ffee",
    fingerprint:
      "7b43207acd291f2db19a5fc3c4cabdd88e297c0d2c48307b6d35a4659fa047e7",
    decision: "higher_margin_alternative",
    outcome: "Higher-margin future selected",
    outcomeDetail:
      "GuardianSim kept the task safe while increasing measured execution clearance from 45.0 mm to 98.5 mm. The largest-clearance decoy failed the frozen stability gate.",
    outcomeTone: "safe",
    futures: [
      {
        id: "A",
        label: "Nominal",
        action: "Yaw 0° · direct approach",
        clearance: "45.0 mm",
        stability: "0.902",
        verdict: "ELIGIBLE",
        reason: "Safe, but lower margin",
        tone: "warning",
        trajectory: "straight",
      },
      {
        id: "B",
        label: "Clearance decoy",
        action: "Yaw −45° · retreat 25 mm",
        clearance: "114.7 mm",
        stability: "0.605",
        verdict: "REJECTED",
        reason: "Below 0.700 stability gate",
        tone: "danger",
        trajectory: "right",
      },
      {
        id: "C",
        label: "Guardian choice",
        action: "Yaw −22.5° · retreat 25 mm",
        clearance: "98.4 mm",
        stability: "0.785",
        verdict: "SELECTED",
        reason: "Higher margin, all gates passed",
        tone: "safe",
        trajectory: "left",
      },
    ],
  },
  stop: {
    eyebrow: "IMPOSSIBLE GAP · GATE 3.3 BREADTH CHECK",
    seed: 509,
    title: "Sometimes the safest motion is no motion.",
    prompt:
      "A 6 mm gap and bounded pose uncertainty leave no certified candidate. Should the robot move anyway?",
    scene: "Lemon pick · 6 mm gap · bearing shift −35° · seed 509",
    protocol: "Schema 6 · strictly validated 12-case partial study",
    sourceLabel: "Inspect Seed 509 in the strict partial report",
    sourceUrl: GATE_33_REPORT,
    reportHash:
      "423310b02e96f17eb6ee813527b1c39270179dc2af14e3a75035eef13226b80e",
    fingerprint:
      "250034a3b5a58854406cae072db7eb2ec172d2b3b6fa42eb428cfb3e0a7214db",
    decision: "safe_stop",
    outcome: "SAFE STOP",
    outcomeDetail:
      "Every tested motion failed at least one frozen hard gate. GuardianSim refused to execute rather than convert uncertainty into contact.",
    outcomeTone: "warning",
    futures: [
      {
        id: "A",
        label: "Nominal",
        action: "Yaw 0° · direct approach",
        clearance: "−2.38 mm",
        stability: "0.933",
        verdict: "COLLISION",
        reason: "Physical overlap",
        tone: "danger",
        trajectory: "straight",
      },
      {
        id: "B",
        label: "Narrow pass",
        action: "Yaw +90° · no retreat",
        clearance: "8.29 mm*",
        stability: "0.000",
        verdict: "REJECTED",
        reason: "Certified margin below 10 mm",
        tone: "danger",
        trajectory: "left",
      },
      {
        id: "C",
        label: "Wide retreat",
        action: "Yaw +90° · retreat 25 mm",
        clearance: "28.6 mm*",
        stability: "0.008",
        verdict: "REJECTED",
        reason: "Stability gate failed",
        tone: "warning",
        trajectory: "right",
      },
    ],
  },
};

const architecture = [
  ["01", "Freeze time", "Fingerprint one physical state before any action."],
  ["02", "Split futures", "Restore it and evaluate 18 bounded approaches."],
  ["03", "Apply hard gates", "Reject overlap, low clearance, instability, or failure."],
  ["04", "Demand repeatability", "One unsafe replay invalidates the candidate."],
  ["05", "Move or stop", "Choose an eligible future—or refuse to move."],
];

function MiniScene({
  trajectory,
  active,
}: {
  trajectory: Future["trajectory"];
  active: boolean;
}) {
  return (
    <div className={`mini-scene trajectory-${trajectory} ${active ? "is-running" : ""}`}>
      <div className="scene-grid" />
      <div className="scene-table" />
      <div className="scene-fruit fruit-target" />
      <div className="scene-fruit fruit-obstacle" />
      <div className="robot-base" />
      <div className="robot-arm arm-one" />
      <div className="robot-arm arm-two" />
      <div className="robot-gripper" />
      <div className="future-path">
        <i />
        <i />
        <i />
        <i />
      </div>
    </div>
  );
}

export function ShowcaseClient() {
  const [challengeKey, setChallengeKey] =
    useState<ChallengeKey>("collision");
  const [phase, setPhase] = useState<Phase>("idle");
  const [guess, setGuess] = useState<string | null>(null);
  const [receiptOpen, setReceiptOpen] = useState(false);

  const challenge = challenges[challengeKey];
  const selectedFuture = challenge.futures.find(
    (future) => future.verdict === "SELECTED",
  );

  const humanResult = useMemo(() => {
    if (!guess || phase !== "revealed") return null;
    if (challenge.decision === "safe_stop") {
      return "GuardianSim found no eligible future. The correct answer was SAFE STOP.";
    }
    return guess === selectedFuture?.id
      ? "You chose the same future as GuardianSim."
      : `You chose Future ${guess}. GuardianSim selected Future ${selectedFuture?.id}.`;
  }, [challenge.decision, guess, phase, selectedFuture?.id]);

  function chooseChallenge(key: ChallengeKey) {
    setChallengeKey(key);
    setPhase("idle");
    setGuess(null);
    setReceiptOpen(false);
  }

  function runFutures() {
    if (phase === "running") return;
    setPhase("running");
    setReceiptOpen(false);
    window.setTimeout(() => {
      setPhase("revealed");
      setReceiptOpen(true);
    }, 1450);
  }

  function rewind() {
    setPhase("idle");
    setGuess(null);
    setReceiptOpen(false);
  }

  function downloadReceipt() {
    const payload = {
      product: "GuardianSim: Parallel Futures",
      claim_boundary: "Genesis simulation; not a physical-robot deployment claim",
      source: challenge.sourceLabel,
      seed: challenge.seed,
      scene: challenge.scene,
      protocol: challenge.protocol,
      decision: challenge.decision,
      outcome: challenge.outcome,
      report_sha256: challenge.reportHash,
      base_snapshot_fingerprint: challenge.fingerprint,
      futures: challenge.futures,
    };
    const blob = new Blob([`${JSON.stringify(payload, null, 2)}\n`], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `guardiansim-seed-${challenge.seed}-evidence-receipt.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="GuardianSim home">
          <span className="brand-mark">G</span>
          <span>GUARDIANSIM</span>
        </a>
        <nav aria-label="Primary navigation">
          <a href="#arena">Arena</a>
          <a href="#replay">Replay</a>
          <a href="#proof">Proof</a>
        </nav>
        <a
          className="github-button"
          href="https://github.com/nvm-star-max/GuardianSim"
          target="_blank"
          rel="noreferrer"
        >
          Source ↗
        </a>
      </header>

      <section className="hero" id="top">
        <div className="hero-grid" aria-hidden="true" />
        <div className="hero-copy">
          <p className="kicker">GUARDIANSIM · PARALLEL FUTURES</p>
          <h1>
            See three futures
            <br />
            <span>before the robot moves.</span>
          </h1>
          <p className="hero-lede">
            A counterfactual safety time machine for robot manipulation,
            evaluated in Genesis on an AMD Radeon GPU.
          </p>
          <div className="hero-actions">
            <a className="primary-action" href="#arena">
              Break the robot <span>↓</span>
            </a>
            <a className="secondary-action" href="#replay">
              Watch the real replay
            </a>
          </div>
        </div>
        <div className="hero-manifesto">
          <span>ONE STATE</span>
          <i />
          <span>18 FUTURES</span>
          <i />
          <span>MOVE OR STOP</span>
        </div>
        <div className="hero-score" aria-label="Verified Gate 3.2 result">
          <span>FROZEN GATE 3.2</span>
          <strong>30 / 30</strong>
          <p>repeatable safe scenarios</p>
          <div>
            <b>58/90 → 90/90</b>
            <small>independent safe executions</small>
          </div>
        </div>
      </section>

      <section className="arena-section" id="arena">
        <div className="section-heading arena-heading">
          <div>
            <p className="kicker dark">INTERACTIVE RED-TEAM ARENA</p>
            <h2>Try to break GuardianSim.</h2>
          </div>
          <p>
            Pick the future you would execute, then run the frozen safety
            gates. Every number below comes from preserved Genesis evidence.
          </p>
        </div>

        <div className="challenge-tabs" role="tablist" aria-label="Verified challenges">
          <button
            type="button"
            role="tab"
            aria-selected={challengeKey === "collision"}
            onClick={() => chooseChallenge("collision")}
          >
            <span>01</span>
            Collision trap
            <b>Seed 411</b>
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={challengeKey === "margin"}
            onClick={() => chooseChallenge("margin")}
          >
            <span>02</span>
            Clearance decoy
            <b>Seed 401</b>
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={challengeKey === "stop"}
            onClick={() => chooseChallenge("stop")}
          >
            <span>03</span>
            Impossible gap
            <b>Seed 509</b>
          </button>
        </div>

        <div className="arena-shell">
          <div className="arena-topline">
            <div>
              <span>{challenge.eyebrow}</span>
              <h3>{challenge.title}</h3>
            </div>
            <div className="scene-identity">
              <span>SCENE</span>
              <b>{challenge.scene}</b>
              <small>{challenge.protocol}</small>
            </div>
          </div>

          <div className="challenge-prompt">
            <span>YOUR MOVE</span>
            <p>{challenge.prompt}</p>
          </div>

          <div className={`future-grid phase-${phase}`} aria-live="polite">
            {challenge.futures.map((future) => {
              const revealed = phase === "revealed";
              return (
                <button
                  type="button"
                  className={`future-card ${
                    revealed ? `future-${future.tone}` : ""
                  } ${guess === future.id ? "is-guessed" : ""}`}
                  key={`${challengeKey}-${future.id}`}
                  onClick={() => phase === "idle" && setGuess(future.id)}
                  aria-pressed={guess === future.id}
                  disabled={phase === "running"}
                >
                  <div className="future-number">
                    <span>FUTURE {future.id}</span>
                    <b>{guess === future.id ? "YOUR PICK" : future.label}</b>
                  </div>
                  <MiniScene
                    trajectory={future.trajectory}
                    active={phase === "running"}
                  />
                  <div className="future-data">
                    <p>{future.action}</p>
                    <div>
                      <span>
                        CLEARANCE <b>{revealed ? future.clearance : "—"}</b>
                      </span>
                      <span>
                        STABILITY <b>{revealed ? future.stability : "—"}</b>
                      </span>
                    </div>
                  </div>
                  <div className="future-verdict">
                    <strong>{revealed ? future.verdict : "UNSEEN"}</strong>
                    <span>{revealed ? future.reason : "Run the counterfactual"}</span>
                  </div>
                </button>
              );
            })}
          </div>

          <div className="arena-controls">
            <div className="run-status" aria-live="polite">
              <span className={`status-light status-${phase}`} />
              {phase === "idle" && "Snapshot frozen. Choose a future or let GuardianSim decide."}
              {phase === "running" && "Restoring one state · evaluating bounded futures · applying hard gates…"}
              {phase === "revealed" && humanResult}
            </div>
            <div>
              {phase === "revealed" && (
                <button className="rewind-button" type="button" onClick={rewind}>
                  ↶ Rewind
                </button>
              )}
              <button
                className="run-button"
                type="button"
                onClick={runFutures}
                disabled={phase === "running" || phase === "revealed"}
              >
                {phase === "running"
                  ? "EVALUATING 18 FUTURES…"
                  : phase === "revealed"
                    ? "DECISION REVEALED"
                    : "RUN 18 FUTURES"}
              </button>
            </div>
          </div>

          {phase === "revealed" && (
            <div className={`decision-banner decision-${challenge.outcomeTone}`}>
              <div>
                <span>GUARDIAN DECISION · {challenge.decision}</span>
                <h3>{challenge.outcome}</h3>
                <p>{challenge.outcomeDetail}</p>
              </div>
              <button type="button" onClick={() => setReceiptOpen((value) => !value)}>
                {receiptOpen ? "Hide receipt" : "Open evidence receipt"} ↗
              </button>
            </div>
          )}

          {receiptOpen && phase === "revealed" && (
            <aside className="receipt" aria-label="GuardianSim evidence receipt">
              <div className="receipt-stamp">VERIFIED<br />EVIDENCE</div>
              <div>
                <span>GUARDIANSIM DECISION RECEIPT</span>
                <h3>Seed {challenge.seed} · {challenge.decision}</h3>
                <dl>
                  <div>
                    <dt>Scene identity</dt>
                    <dd>{challenge.fingerprint}</dd>
                  </div>
                  <div>
                    <dt>Report SHA-256</dt>
                    <dd>{challenge.reportHash}</dd>
                  </div>
                  <div>
                    <dt>Claim boundary</dt>
                    <dd>Genesis simulation · not a physical-robot deployment claim</dd>
                  </div>
                </dl>
              </div>
              <div className="receipt-actions">
                <a href={challenge.sourceUrl} target="_blank" rel="noreferrer">
                  Audit source ↗
                </a>
                <button type="button" onClick={downloadReceipt}>
                  Download JSON ↓
                </button>
              </div>
            </aside>
          )}
          {challengeKey === "stop" && (
            <p className="certified-note">
              * Seed 509 values use the schema-6 certified lower bound after
              bounded relative-position uncertainty.
            </p>
          )}
        </div>
      </section>

      <section className="replay-section" id="replay">
        <div className="section-heading replay-heading">
          <div>
            <p className="kicker">ONE REPLAY FOR CLARITY</p>
            <h2>Watch the timeline split.</h2>
          </div>
          <p>
            Seed 411 starts from the same state. The nominal path overlaps the
            plum; GuardianSim rotates the approach and preserves 17.1 mm.
          </p>
        </div>
        <div className="video-shell">
          <video
            controls
            muted
            loop
            playsInline
            poster="/seed-411-preview.png"
            preload="metadata"
          >
            <source src="/seed-411-parallel-futures.mp4" type="video/mp4" />
          </video>
          <div className="video-legend">
            <span><i className="legend-red" /> Nominal · 1.42 mm overlap</span>
            <span><i className="legend-green" /> GuardianSim · 17.1 mm clearance</span>
            <span>Same task · same initial state · formal seed 411</span>
          </div>
        </div>
      </section>

      <section className="proof-section" id="proof">
        <div className="section-heading proof-heading">
          <div>
            <p className="kicker dark">FROZEN 30-SCENARIO BENCHMARK</p>
            <h2>One scene is the hook. Thirty scenes are the claim.</h2>
          </div>
          <p>
            The interactive arena illustrates preserved episodes. Performance
            claims come only from the complete schema-5 report.
          </p>
        </div>

        <div className="metric-grid">
          <article className="metric-card metric-hero">
            <span>REPEATABLE SAFE SCENARIOS</span>
            <div><b>18/30</b><i>→</i><strong>30/30</strong></div>
            <p>Every GuardianSim scenario passed all three executions.</p>
          </article>
          <article className="metric-card">
            <span>INDEPENDENT SAFE EXECUTIONS</span>
            <div><b>58/90</b><i>→</i><strong>90/90</strong></div>
            <p>Three physical executions per strategy and scenario.</p>
          </article>
          <article className="metric-card">
            <span>CLUTTER CONTACT EXECUTIONS</span>
            <div><b>30</b><i>→</i><strong>0</strong></div>
            <p>Measured sampled clutter contacts in Genesis.</p>
          </article>
          <article className="metric-card">
            <span>MEAN SAMPLED CLEARANCE</span>
            <div><b>23.191</b><i>→</i><strong>46.003 mm</strong></div>
            <p>+98.36% versus the nominal baseline.</p>
          </article>
        </div>

        <div className="architecture-grid">
          {architecture.map(([number, title, body]) => (
            <article key={number}>
              <span>{number}</span>
              <h3>{title}</h3>
              <p>{body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="evidence-cta">
        <div>
          <p className="kicker">AUDIT THE CLAIM</p>
          <h2>No magic numbers. Just preserved evidence.</h2>
        </div>
        <div className="evidence-links">
          <a href={GATE_32_REPORT} target="_blank" rel="noreferrer">
            Frozen schema-5 report <span>↗</span>
          </a>
          <a
            href="https://github.com/nvm-star-max/GuardianSim/tree/25e27aced13237b5af93fd91697d7abb12101a30/docs/evidence/gate-3-2"
            target="_blank"
            rel="noreferrer"
          >
            Raw logs & checksums <span>↗</span>
          </a>
          <a
            href="https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/39"
            target="_blank"
            rel="noreferrer"
          >
            Official Track 3 submission <span>↗</span>
          </a>
        </div>
      </section>

      <footer>
        <div className="brand">
          <span className="brand-mark">G</span>
          <span>GUARDIANSIM · AEGIS MOTION</span>
        </div>
        <p>
          Genesis simulation · AMD Radeon GPU · ROCm/HIP
          <br />
          No physical-robot deployment claim.
        </p>
        <span>See three futures before the robot moves.</span>
      </footer>
    </main>
  );
}
