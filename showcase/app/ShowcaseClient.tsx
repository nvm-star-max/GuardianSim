"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  safetySwarmFormal,
  safetySwarmRows,
} from "./safetySwarmFormal.generated";

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
const SAFETY_SWARM_V2_REPORT =
  "https://github.com/nvm-star-max/GuardianSim/blob/975a82b3e09d0458a4c02ac945859f2fdf874c4f/docs/evidence/safety-swarm-v2-formal-2026-07-30/formal-report.json";
const SAFETY_SWARM_V2_EVIDENCE =
  "https://github.com/nvm-star-max/GuardianSim/tree/975a82b3e09d0458a4c02ac945859f2fdf874c4f/docs/evidence/safety-swarm-v2-formal-2026-07-30";

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

const scaleSteps = [
  { worlds: "1", throughput: "154", speedup: "1.00×" },
  { worlds: "16", throughput: "2,384", speedup: "15.47×" },
  { worlds: "64", throughput: "9,354", speedup: "60.69×" },
  { worlds: "256", throughput: "35,166", speedup: "228.16×" },
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

const swarmOutcomeColors = {
  S: "#54f58b",
  C: "#ff6858",
  M: "#ffc857",
  G: "#73b9ff",
  U: "#be8cff",
  T: "#e9edf3",
} as const;

function SafetySwarmHeatmap() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const context = canvas.getContext("2d");
    if (!context) return;

    const width = 1440;
    const height = 560;
    const matrixLeft = 205;
    const matrixTop = 58;
    const matrixWidth = 1024;
    const rowStep = 25;
    const cellWidth = matrixWidth / safetySwarmFormal.worldCountPerCandidate;

    canvas.width = width;
    canvas.height = height;
    context.clearRect(0, 0, width, height);
    context.fillStyle = "#02090d";
    context.fillRect(0, 0, width, height);

    context.font = "700 15px ui-monospace, SFMono-Regular, Menlo, monospace";
    context.fillStyle = "#8ca0ac";
    context.fillText("CANDIDATE", 22, 33);
    context.fillText("UNCERTAINTY WORLD 0", matrixLeft, 33);
    context.textAlign = "right";
    context.fillText("255", matrixLeft + matrixWidth, 33);
    context.fillText("SAFE / 256", 1408, 33);
    context.textAlign = "left";

    for (let tick = 0; tick <= 256; tick += 32) {
      const x = matrixLeft + tick * cellWidth;
      context.strokeStyle = "rgba(115, 185, 255, 0.13)";
      context.beginPath();
      context.moveTo(x, matrixTop - 8);
      context.lineTo(x, matrixTop + safetySwarmRows.length * rowStep - 7);
      context.stroke();
    }

    safetySwarmRows.forEach((row, rowIndex) => {
      const y = matrixTop + rowIndex * rowStep;

      if (row.selected) {
        context.fillStyle = "rgba(216, 255, 95, 0.08)";
        context.fillRect(10, y - 4, width - 20, rowStep - 1);
        context.fillStyle = "#d8ff5f";
        context.fillRect(10, y - 4, 5, rowStep - 1);
      }

      context.font = row.selected
        ? "800 14px ui-monospace, SFMono-Regular, Menlo, monospace"
        : "600 14px ui-monospace, SFMono-Regular, Menlo, monospace";
      context.fillStyle = row.selected ? "#d8ff5f" : "#aab8c1";
      context.fillText(
        `${String(row.candidateIndex + 1).padStart(2, "0")}  ${row.label}`,
        22,
        y + 11,
      );

      Array.from(row.outcomes).forEach((outcome, worldIndex) => {
        context.fillStyle =
          swarmOutcomeColors[outcome as keyof typeof swarmOutcomeColors] ??
          "#47525a";
        context.fillRect(
          matrixLeft + worldIndex * cellWidth,
          y,
          Math.max(2.8, cellWidth - 0.6),
          15,
        );
      });

      context.textAlign = "right";
      context.fillStyle = row.qualifies ? "#54f58b" : "#93a4ae";
      context.fillText(
        `${row.safeWorldCount}${row.qualifies ? "  PASS" : ""}`,
        1408,
        y + 11,
      );
      context.textAlign = "left";
    });

    context.strokeStyle = "rgba(255, 255, 255, 0.13)";
    context.strokeRect(
      matrixLeft - 1,
      matrixTop - 1,
      matrixWidth + 2,
      safetySwarmRows.length * rowStep - 9,
    );
  }, []);

  return (
    <div className="swarm-heatmap-shell">
      <div className="swarm-heatmap-scroll">
        <canvas
          ref={canvasRef}
          className="swarm-heatmap-canvas"
          role="img"
          aria-label="Safety Swarm V2 formal matrix: 18 candidate actions by 256 uncertainty worlds. Five candidates pass all worlds and candidate five is selected."
        />
      </div>
      <div className="swarm-legend" aria-label="Heatmap outcome legend">
        <span><i className="legend-safe" /> Safe</span>
        <span><i className="legend-contact" /> Clutter contact</span>
        <span><i className="legend-stability" /> Stability gate</span>
        <span><i className="legend-clearance" /> Clearance gate</span>
        <b>Each pixel is one measured candidate-by-world result.</b>
      </div>
      <ol className="sr-only">
        {safetySwarmRows.map((row) => (
          <li key={row.candidateId}>
            Candidate {row.candidateIndex + 1}, {row.label}:{" "}
            {row.safeWorldCount} of 256 worlds safe
            {row.qualifies ? ", qualified" : ", rejected"}
            {row.selected ? ", selected for execution" : ""}.
          </li>
        ))}
      </ol>
    </div>
  );
}

function SafetySwarmFormalSection() {
  const selected = safetySwarmRows.find((row) => row.selected);

  return (
    <div className="swarm-formal-stage" id="formal">
      <div className="swarm-formal-heading">
        <div>
          <span>SAFETY SWARM V2 · FROZEN FORMAL RUN</span>
          <h3>18 actions. 256 uncertain worlds each.</h3>
          <p>
            Every candidate faced the same bounded uncertainty set in one
            Radeon batch. A candidate survived only if all 256 worlds passed
            the frozen hard gates.
          </p>
        </div>
        <div className="swarm-funnel" aria-label="Safety Swarm decision funnel">
          <div>
            <strong>4,608</strong>
            <span>measured candidate-world pairs</span>
          </div>
          <i>→</i>
          <div>
            <strong>5</strong>
            <span>candidates passed 256/256</span>
          </div>
          <i>→</i>
          <div className="swarm-funnel-selected">
            <strong>1</strong>
            <span>frozen ranking selected</span>
          </div>
        </div>
      </div>

      <SafetySwarmHeatmap />

      <div className="swarm-formal-bottom">
        <article className="swarm-decision-card">
          <span>EXECUTE</span>
          <h4>{selected?.label}</h4>
          <p>{selected?.safeWorldCount}/256 worlds safe · zero clutter contacts</p>
          <dl>
            <div>
              <dt>Worst clearance</dt>
              <dd>{selected?.worstCaseClearanceMm.toFixed(3)} mm</dd>
            </div>
            <div>
              <dt>5th percentile</dt>
              <dd>{selected?.fifthPercentileClearanceMm.toFixed(3)} mm</dd>
            </div>
            <div>
              <dt>Minimum stability</dt>
              <dd>{selected?.minimumStability.toFixed(3)}</dd>
            </div>
          </dl>
        </article>

        <article className="swarm-compute-card">
          <span>AMD RADEON FORMAL WORKLOAD</span>
          <strong>10,143.979</strong>
          <p>measured environment steps per second</p>
          <dl>
            <div>
              <dt>Physics steps</dt>
              <dd>2,299,392</dd>
            </div>
            <div>
              <dt>Execution wall time</dt>
              <dd>226.676 s</dd>
            </div>
            <div>
              <dt>GPU utilization</dt>
              <dd>73.406% mean · 97% peak</dd>
            </div>
            <div>
              <dt>Runtime</dt>
              <dd>ROCm/HIP · Genesis 1.2.3</dd>
            </div>
          </dl>
        </article>

        <article className="swarm-audit-card">
          <span>WHAT WAS REJECTED</span>
          <strong>1,994</strong>
          <p>candidate-world pairs failed at least one frozen gate.</p>
          <dl>
            <div><dt>Stability gate</dt><dd>1,691</dd></div>
            <div><dt>Clutter contact</dt><dd>270</dd></div>
            <div><dt>Clearance gate</dt><dd>33</dd></div>
          </dl>
          <a href={SAFETY_SWARM_V2_REPORT} target="_blank" rel="noreferrer">
            Inspect the immutable report ↗
          </a>
        </article>
      </div>

      <small className="swarm-boundary">
        Engineering candidate-by-uncertainty simulation stress test on AMD
        Radeon Cloud · not 4,608 independent robot trials and not a
        physical-robot safety guarantee
      </small>
    </div>
  );
}

function RadeonScaleSection() {
  return (
    <section className="radeon-scale-section" id="scale">
      <div className="section-heading scale-heading">
        <div>
          <p className="kicker">RADEON PARALLEL PHYSICS LAB</p>
          <h2>One GPU. 256 robot worlds.</h2>
        </div>
        <p>
          Strictly validated on Radeon Cloud with real Genesis physics. Scale
          evidence is reported separately from the formal safety sample count.
        </p>
      </div>

      <div className="scale-progression" aria-label="Measured Radeon scaling progression">
        {scaleSteps.map((step, index) => (
          <article key={step.worlds} className={index === scaleSteps.length - 1 ? "scale-peak" : ""}>
            <span>{String(index + 1).padStart(2, "0")} · BATCH</span>
            <strong>{step.worlds}</strong>
            <p>parallel worlds</p>
            <dl>
              <div>
                <dt>Throughput</dt>
                <dd>{step.throughput}</dd>
              </div>
              <div>
                <dt>Speedup</dt>
                <dd>{step.speedup}</dd>
              </div>
            </dl>
          </article>
        ))}
      </div>

      <div className="radeon-scale-shell">
        <div className="future-wall" aria-label="Measured 256-world Radeon batch">
          {Array.from({ length: 256 }, (_, index) => (
            <i
              key={index}
              className={index % 19 === 0 ? "future-hot" : ""}
              aria-hidden="true"
            />
          ))}
          <div className="future-wall-label">
            <span>256 SIMULTANEOUS FRANKA WORLDS</span>
            <b>337,000 measured environment steps</b>
          </div>
        </div>
        <div className="scale-console">
          <span>STRICT VALIDATION PASSED</span>
          <strong>35,166 env-steps/s</strong>
          <p>256 headless Franka worlds on one AMD Radeon GPU</p>
          <dl>
            <div><dt>Speedup vs 1 world</dt><dd>228.16×</dd></div>
            <div><dt>Parallel efficiency</dt><dd>89.1%</dd></div>
            <div><dt>GPU use</dt><dd>85.5% mean · 96% peak</dd></div>
            <div><dt>Measured workload</dt><dd>337,000 env-steps</dd></div>
          </dl>
          <small>
            Physics throughput benchmark · not 337,000 independent safety trials
          </small>
        </div>
      </div>

      <SafetySwarmFormalSection />
    </section>
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
          <a href="#scale">Radeon Scale</a>
          <a href="#formal">4,608 Run</a>
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
          <p className="kicker">AMD RADEON · PARALLEL PHYSICAL AI</p>
          <h1>
            4,608 futures.
            <br />
            <span>One action.</span>
          </h1>
          <p className="hero-lede">
            GuardianSim stress-tests 18 actions across 256 uncertainty worlds
            on Radeon, then explains why one action executes—or why none should.
          </p>
          <div className="hero-actions">
            <a className="primary-action" href="#scale">
              Enter the parallel lab <span>↓</span>
            </a>
            <a className="secondary-action" href="#arena">
              Try the safety arena
            </a>
          </div>
        </div>
        <div className="hero-manifesto">
          <span>ONE RADEON GPU</span>
          <i />
          <span>18 BOUNDED ACTIONS</span>
          <i />
          <span>256 WORLDS EACH</span>
          <i />
          <span>MOVE OR STOP</span>
        </div>
        <div className="hero-score" aria-label="Preserved evidence scale">
          <span>FROZEN 4,608-PAIR RUN</span>
          <strong>10,144</strong>
          <p>environment steps per second · formal workload</p>
          <div>
            <b>2.30M measured physics steps</b>
            <small>73.4% mean GPU · 97% peak GPU</small>
          </div>
        </div>
      </section>

      <RadeonScaleSection />

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
                        CLEARANCE <b>{future.clearance}</b>
                      </span>
                      <span>
                        STABILITY <b>{future.stability}</b>
                      </span>
                    </div>
                  </div>
                  <div className="future-verdict">
                    <strong>
                      {revealed
                        ? future.verdict
                        : phase === "running"
                          ? "EVALUATING"
                          : "MEASURED"}
                    </strong>
                    <span>
                      {revealed
                        ? future.reason
                        : phase === "running"
                          ? "Applying frozen hard gates"
                          : "Choose, then apply the gates"}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>

          <div className="arena-controls">
            <div className="run-status" aria-live="polite">
              <span className={`status-light status-${phase}`} />
              {phase === "idle" &&
                "Verified measurements loaded. Choose a future, then apply the frozen gates."}
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
                  ? "CHECKING 18 FUTURES…"
                  : phase === "revealed"
                    ? "DECISION REVEALED"
                    : "APPLY GATES TO 18 FUTURES"}
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
            poster="seed-411-preview.png"
            preload="metadata"
          >
            <source src="seed-411-parallel-futures.mp4" type="video/mp4" />
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
            <h2>Count the scenes. Audit every nested trace.</h2>
          </div>
          <p>
            The interactive arena illustrates preserved episodes. Performance
            claims come only from the complete schema-5 report.
          </p>
        </div>

        <div className="scale-ledger" aria-label="Preserved evidence scale">
          <article>
            <span>INDEPENDENT SCENE UNITS</span>
            <strong>42</strong>
            <p>30 formal Gate 3.2 + 12 engineering-breadth Gate 3.3 scenes.</p>
          </article>
          <article>
            <span>COUNTERFACTUAL ROLLOUTS</span>
            <strong>1,185</strong>
            <p>Initial candidates plus additional confirmation rollouts.</p>
          </article>
          <article>
            <span>FINAL EXECUTIONS</span>
            <strong>202</strong>
            <p>Baseline and GuardianSim actions physically executed in Genesis.</p>
          </article>
          <article className="scale-total">
            <span>TOTAL SIMULATED ACTION TRACES</span>
            <strong>1,387</strong>
            <p>Nested inside 42 scenes; never presented as 1,387 independent trials.</p>
          </article>
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
          <a href={SAFETY_SWARM_V2_REPORT} target="_blank" rel="noreferrer">
            Safety Swarm V2 · 4,608-pair report <span>↗</span>
          </a>
          <a href={SAFETY_SWARM_V2_EVIDENCE} target="_blank" rel="noreferrer">
            V2 raw logs, validation & checksums <span>↗</span>
          </a>
          <a href={GATE_32_REPORT} target="_blank" rel="noreferrer">
            Frozen 30-scenario report <span>↗</span>
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
        <span>Test 4,608 futures before one action moves.</span>
      </footer>
    </main>
  );
}
