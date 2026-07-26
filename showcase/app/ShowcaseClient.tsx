"use client";

import { useMemo, useState } from "react";

type StoryKey = "failure" | "fix" | "proof";

const stories: Record<
  StoryKey,
  {
    eyebrow: string;
    title: string;
    body: string;
    stat: string;
    statLabel: string;
  }
> = {
  failure: {
    eyebrow: "GATE 3.1 · NEGATIVE EVIDENCE",
    title: "More clearance did not mean safer execution.",
    body:
      "The first adversarial benchmark improved mean clearance by 43.67%, yet GuardianSim completed only 18/30 scenarios safely versus 19/30 for the nominal baseline. We kept the failure and traced it to a narrow action family and unsafe fallback behavior.",
    stat: "18 / 30",
    statLabel: "repeatable safe completions",
  },
  fix: {
    eyebrow: "GATE 3.2 · FROZEN BEFORE RUNNING",
    title: "Expand the action space. Require repeatable proof.",
    body:
      "The frozen policy evaluates 18 obstacle-aware approaches, confirms physical execution three times, replaces unsafe nominal actions, and safe-stops when no candidate has sufficient evidence.",
    stat: "18 × 3",
    statLabel: "actions × execution checks",
  },
  proof: {
    eyebrow: "GATE 3.2 · VERIFIED OUTCOME",
    title: "Every GuardianSim scenario passed all three executions.",
    body:
      "Across 30 unseen scenarios and 90 independent physical executions, GuardianSim achieved 30/30 repeatable safe completion, eliminated clutter contacts, and nearly doubled mean clearance.",
    stat: "30 / 30",
    statLabel: "repeatable safe completions",
  },
};

const decisionRows = [
  { label: "Higher-margin alternative", count: 11, tone: "coral" },
  { label: "Unsafe nominal replaced", count: 10, tone: "blue" },
  { label: "Eligible nominal fallback", count: 9, tone: "mint" },
];

const recoveryCells = [
  {
    cell: "Lemon · lateral clutter",
    baseline: "0 / 5",
    guardian: "5 / 5",
  },
  {
    cell: "Plum · lateral clutter",
    baseline: "0 / 5",
    guardian: "5 / 5",
  },
  {
    cell: "Lemon + plum · radial",
    baseline: "8 / 10",
    guardian: "10 / 10",
  },
];

const architecture = [
  [
    "01",
    "Snapshot",
    "Capture robot and object state, then bind every episode to a SHA-256 scene fingerprint.",
  ],
  [
    "02",
    "Counterfactuals",
    "Restore the same snapshot and evaluate 18 yaw, retreat, and approach combinations.",
  ],
  [
    "03",
    "Physical evidence",
    "Measure reachability, retained lift, clutter overlap, clearance, and execution time.",
  ],
  [
    "04",
    "Repeatability",
    "Require three independent executions; one unsafe replay invalidates repeatable completion.",
  ],
  [
    "05",
    "Safety-first choice",
    "Replace unsafe nominal actions, prefer higher margin, or safe-stop when evidence is weak.",
  ],
];

export function ShowcaseClient() {
  const [story, setStory] = useState<StoryKey>("proof");
  const [presenter, setPresenter] = useState(false);
  const activeStory = stories[story];

  const storyOrder = useMemo(
    () => ["failure", "fix", "proof"] as StoryKey[],
    [],
  );

  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="GuardianSim home">
          <span className="brand-mark">G</span>
          <span>GUARDIANSIM</span>
        </a>
        <nav aria-label="Primary navigation">
          <a href="#method">Method</a>
          <a href="#evidence">Evidence</a>
          <a href="#architecture">Architecture</a>
        </nav>
        <button
          className="presenter-button"
          type="button"
          onClick={() => setPresenter((value) => !value)}
          aria-pressed={presenter}
        >
          {presenter ? "Exit 90s mode" : "90s presenter mode"}
        </button>
      </header>

      <section className="hero" id="top">
        <div className="hero-grid" aria-hidden="true" />
        <div className="hero-copy">
          <p className="kicker">AMD AI DEVMASTER · TRACK 3 PHYSICAL AI</p>
          <h1>
            Choose safer.
            <br />
            <span>Prove it.</span>
          </h1>
          <p className="hero-lede">
            An auditable counterfactual safety layer for robot manipulation,
            validated in Genesis on an AMD Radeon GPU.
          </p>
          <div className="hero-actions">
            <a className="primary-action" href="#evidence">
              Inspect the evidence <span>↘</span>
            </a>
            <a
              className="secondary-action"
              href="https://github.com/nvm-star-max/GuardianSim"
              target="_blank"
              rel="noreferrer"
            >
              GitHub ↗
            </a>
          </div>
        </div>

        <div className="hero-score" aria-label="Verified Gate 3.2 score">
          <div className="score-orbit orbit-one" />
          <div className="score-orbit orbit-two" />
          <div className="score-core">
            <span className="score-label">SCHEMA-5 VERIFIED</span>
            <strong>30/30</strong>
            <span>repeatable safe scenarios</span>
          </div>
          <div className="score-tag tag-clearance">
            <b>+40 pp</b>
            <span>safe-completion lift</span>
          </div>
          <div className="score-tag tag-observations">
            <b>0</b>
            <span>Guardian clutter contacts</span>
          </div>
        </div>

        <div className="hero-proofline">
          <span>01</span>
          <p>
            Unseen seeds 401–430.
            <br />
            Frozen protocol and thresholds.
          </p>
          <div className="proofline-rule" />
          <p className="proofline-note">
            Simulation evidence,
            <br />
            not a physical deployment claim.
          </p>
        </div>
      </section>

      {presenter && (
        <aside className="presenter-strip" aria-live="polite">
          <span>90 SEC STORY</span>
          <ol>
            <li>Failure: Gate 3.1 proved that clearance alone was insufficient.</li>
            <li>Method: 18 obstacle-aware actions, each checked three times.</li>
            <li>Proof: 60% → 100% repeatable safety; 30 → 0 contacts.</li>
          </ol>
        </aside>
      )}

      <section className="story-section" id="method">
        <div className="section-heading">
          <p className="kicker dark">THE ENGINEERING STORY</p>
          <h2>Failure became protocol.</h2>
          <p>
            We did not tune away the negative result. We froze a new protocol
            on unseen seeds, then ran it once.
          </p>
        </div>

        <div className="story-shell">
          <div
            className="story-tabs"
            role="tablist"
            aria-label="Engineering story"
          >
            {storyOrder.map((key, index) => (
              <button
                key={key}
                type="button"
                role="tab"
                aria-selected={story === key}
                onClick={() => setStory(key)}
              >
                <span>0{index + 1}</span>
                {key === "failure"
                  ? "Failure"
                  : key === "fix"
                    ? "Protocol"
                    : "Proof"}
              </button>
            ))}
          </div>

          <article className="story-card">
            <div className="story-copy">
              <p className="story-eyebrow">{activeStory.eyebrow}</p>
              <h3>{activeStory.title}</h3>
              <p>{activeStory.body}</p>
            </div>
            <div className={`story-stat story-stat-${story}`}>
              <strong>{activeStory.stat}</strong>
              <span>{activeStory.statLabel}</span>
            </div>
          </article>

          <div className="policy-flow" aria-label="Gate 3.2 safety policy">
            <div>
              <b>1 snapshot</b>
              <span>identical starting state</span>
            </div>
            <i>→</i>
            <div>
              <b>18 actions</b>
              <span>obstacle-aware family</span>
            </div>
            <i>→</i>
            <div>
              <b>× 3</b>
              <span>independent executions</span>
            </div>
            <i>→</i>
            <div>
              <b>Choose / stop</b>
              <span>safety-first decision</span>
            </div>
          </div>
        </div>
      </section>

      <section className="evidence-section" id="evidence">
        <div className="section-heading evidence-heading">
          <p className="kicker">FORMAL BENCHMARK · SEEDS 401–430</p>
          <h2>Measured three times.</h2>
          <p>
            A scenario counts as repeatably safe only when all three physical
            executions pass reachability, stability, contact, and clearance
            checks.
          </p>
        </div>

        <div className="metric-grid">
          <article className="metric-card success-card">
            <div className="metric-topline">
              <span>Repeatable safe completion</span>
              <b>30 scenarios</b>
            </div>
            <div className="success-comparison">
              <div>
                <span>Nominal baseline</span>
                <strong>60%</strong>
                <i style={{ width: "60%" }} />
              </div>
              <div>
                <span>GuardianSim</span>
                <strong>100%</strong>
                <i style={{ width: "100%" }} />
              </div>
            </div>
            <p>18/30 → 30/30 · +40.00 percentage points</p>
          </article>

          <article className="metric-card clearance-card">
            <div className="metric-topline">
              <span>Mean clutter clearance</span>
              <b>metres</b>
            </div>
            <div className="clearance-number">
              <strong>+98.36%</strong>
              <span>vs nominal</span>
            </div>
            <div className="clearance-bars">
              <div>
                <span>0.023191</span>
                <i style={{ width: "50%" }} />
              </div>
              <div>
                <span>0.046003</span>
                <i style={{ width: "100%" }} />
              </div>
            </div>
          </article>

          <article className="metric-card stability-card">
            <div className="metric-topline">
              <span>Clutter contacts</span>
              <b>90 executions each</b>
            </div>
            <div className="contact-values">
              <div>
                <span>Nominal baseline</span>
                <strong>30</strong>
              </div>
              <div>
                <span>GuardianSim</span>
                <strong>0</strong>
              </div>
            </div>
            <p>Independent safe executions: 58/90 → 90/90.</p>
          </article>
        </div>

        <div className="evidence-lower">
          <article className="selection-card">
            <div className="card-heading">
              <div>
                <span>Decision taxonomy</span>
                <h3>30 explainable choices</h3>
              </div>
              <b>every decision accounted for</b>
            </div>
            <div className="selection-rows">
              {decisionRows.map((row) => (
                <div className="selection-row" key={row.label}>
                  <span>{row.label}</span>
                  <div>
                    <i
                      className={`tone-${row.tone}`}
                      style={{ width: `${(row.count / 11) * 100}%` }}
                    />
                  </div>
                  <b>{row.count}</b>
                </div>
              ))}
            </div>
          </article>

          <article className="seed-card">
            <div className="card-heading">
              <div>
                <span>Recovered adversarial cells</span>
                <h3>Baseline → GuardianSim</h3>
              </div>
              <b>repeatable safe scenarios</b>
            </div>
            <div
              className="seed-table"
              role="table"
              aria-label="Recovered adversarial cells"
            >
              {recoveryCells.map((row) => (
                <div role="row" className="seed-row recovery-row" key={row.cell}>
                  <strong role="cell">{row.cell}</strong>
                  <span role="cell">{row.baseline}</span>
                  <span role="cell">→</span>
                  <span role="cell">{row.guardian}</span>
                </div>
              ))}
            </div>
          </article>
        </div>
      </section>

      <section className="architecture-section" id="architecture">
        <div className="section-heading">
          <p className="kicker dark">SYSTEM ARCHITECTURE</p>
          <h2>A safety layer, not a black box.</h2>
          <p>
            Every action is tied to a restored scene, measured physical
            outcomes, and an explicit decision reason.
          </p>
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
          <h2>Every headline number has raw evidence.</h2>
        </div>
        <div className="evidence-links">
          <a
            href="https://github.com/nvm-star-max/GuardianSim/blob/0974313/docs/evidence/gate-3-2/formal-report.json"
            target="_blank"
            rel="noreferrer"
          >
            Inspect schema-5 report <span>↗</span>
          </a>
          <a
            href="https://github.com/nvm-star-max/GuardianSim/tree/0974313/docs/evidence/gate-3-2"
            target="_blank"
            rel="noreferrer"
          >
            Review logs & checksums <span>↗</span>
          </a>
          <a
            href="https://github.com/nvm-star-max/GuardianSim/pull/1"
            target="_blank"
            rel="noreferrer"
          >
            Inspect source & tests <span>↗</span>
          </a>
        </div>
      </section>

      <footer>
        <div className="brand">
          <span className="brand-mark">G</span>
          <span>GUARDIANSIM</span>
        </div>
        <p>
          Genesis simulation · AMD Radeon GPU · ROCm/HIP
          <br />
          No physical-robot deployment claim.
        </p>
        <span>Gate 3.2 evidence frozen · 2026-07-26</span>
      </footer>
    </main>
  );
}
