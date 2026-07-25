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
    eyebrow: "GATE 2.7 · NEGATIVE EVIDENCE",
    title: "High scores hid a repeatability failure.",
    body:
      "A one-shot rollout picked three negative-offset grasps that looked safe in simulation, then produced zero retained-lift stability during independent replay.",
    stat: "17 / 20",
    statLabel: "GuardianSim successes",
  },
  fix: {
    eyebrow: "GATE 2.8 · PREDECLARED POLICY",
    title: "Confirm, aggregate conservatively, then decide.",
    body:
      "All 15 actions are scored once. The top three plus nominal receive two extra rollouts. Weak evidence triggers a nominal fallback instead of an optimistic action.",
    stat: "240",
    statLabel: "confirmation observations",
  },
  proof: {
    eyebrow: "GATE 2.8 · VERIFIED OUTCOME",
    title: "Reliability recovered without giving up safety margin.",
    body:
      "The same 20 seeds produced 20 unique snapshots. Baseline and GuardianSim both succeeded in every independent execution, while GuardianSim kept substantially more space from clutter.",
    stat: "+63.93%",
    statLabel: "mean clutter clearance",
  },
};

const selectionRows = [
  { label: "Yaw −22.5° · offset +0.020 m", count: 10, tone: "coral" },
  { label: "Yaw −22.5° · offset 0.000 m", count: 8, tone: "blue" },
  { label: "Yaw +45.0° · offset +0.020 m", count: 1, tone: "mint" },
  { label: "Nominal · yaw 0°", count: 1, tone: "white" },
];

const failureSeeds = [
  {
    seed: 104,
    candidate: "−22.5° / 0.000 m",
    stability: "0.89350",
    clearance: "0.07901 m",
  },
  {
    seed: 107,
    candidate: "−22.5° / 0.000 m",
    stability: "0.89694",
    clearance: "0.08319 m",
  },
  {
    seed: 120,
    candidate: "−22.5° / +0.020 m",
    stability: "0.90201",
    clearance: "0.05365 m",
  },
];

export function ShowcaseClient() {
  const [story, setStory] = useState<StoryKey>("proof");
  const [presenter, setPresenter] = useState(false);
  const activeStory = stories[story];

  const storyOrder = useMemo(
    () => (["failure", "fix", "proof"] as StoryKey[]),
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
          <p className="kicker">
            AMD AI DEVMASTER · TRACK 3 PHYSICAL AI
          </p>
          <h1>
            Simulate twice.
            <br />
            <span>Fail safely.</span>
          </h1>
          <p className="hero-lede">
            A repeatability-aware safety layer for Franka manipulation,
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

        <div className="hero-score" aria-label="Verified Gate 2.8 score">
          <div className="score-orbit orbit-one" />
          <div className="score-orbit orbit-two" />
          <div className="score-core">
            <span className="score-label">VERIFIED</span>
            <strong>20/20</strong>
            <span>independent executions</span>
          </div>
          <div className="score-tag tag-clearance">
            <b>+63.93%</b>
            <span>clutter clearance</span>
          </div>
          <div className="score-tag tag-observations">
            <b>240</b>
            <span>confirmations</span>
          </div>
        </div>

        <div className="hero-proofline">
          <span>01</span>
          <p>
            Same seeds. Same snapshots.
            <br />
            Predeclared thresholds.
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
            <li>Problem: one-shot simulation looked safe but replay failed.</li>
            <li>Method: repeat top candidates and aggregate the worst case.</li>
            <li>Proof: 20/20 success with 63.93% more clutter clearance.</li>
          </ol>
        </aside>
      )}

      <section className="story-section" id="method">
        <div className="section-heading">
          <p className="kicker dark">THE ENGINEERING STORY</p>
          <h2>We kept the failure.</h2>
          <p>
            Gate 2.7 is not hidden. It is the evidence that shaped Gate 2.8.
          </p>
        </div>

        <div className="story-shell">
          <div className="story-tabs" role="tablist" aria-label="Engineering story">
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
                    ? "Policy"
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

          <div className="policy-flow" aria-label="Robust selection policy">
            <div>
              <b>15</b>
              <span>initial candidates</span>
            </div>
            <i>→</i>
            <div>
              <b>Top 3 + N</b>
              <span>shortlist + nominal</span>
            </div>
            <i>→</i>
            <div>
              <b>× 2</b>
              <span>extra confirmations</span>
            </div>
            <i>→</i>
            <div>
              <b>Worst case</b>
              <span>conservative score</span>
            </div>
          </div>
        </div>
      </section>

      <section className="evidence-section" id="evidence">
        <div className="section-heading evidence-heading">
          <p className="kicker">PAIRED BENCHMARK · SEEDS 101–120</p>
          <h2>Proof, not a promise.</h2>
          <p>
            20 unique scene fingerprints. Independent replay from the same
            episode snapshot.
          </p>
        </div>

        <div className="metric-grid">
          <article className="metric-card success-card">
            <div className="metric-topline">
              <span>Success rate</span>
              <b>20 episodes</b>
            </div>
            <div className="success-comparison">
              <div>
                <span>Nominal</span>
                <strong>100%</strong>
                <i style={{ width: "100%" }} />
              </div>
              <div>
                <span>GuardianSim</span>
                <strong>100%</strong>
                <i style={{ width: "100%" }} />
              </div>
            </div>
            <p>Gate 2.7 GuardianSim: 85% → Gate 2.8: 100%</p>
          </article>

          <article className="metric-card clearance-card">
            <div className="metric-topline">
              <span>Mean clutter clearance</span>
              <b>metres</b>
            </div>
            <div className="clearance-number">
              <strong>+63.93%</strong>
              <span>vs nominal</span>
            </div>
            <div className="clearance-bars">
              <div>
                <span>0.04399</span>
                <i style={{ width: "61%" }} />
              </div>
              <div>
                <span>0.07212</span>
                <i style={{ width: "100%" }} />
              </div>
            </div>
          </article>

          <article className="metric-card stability-card">
            <div className="metric-topline">
              <span>Mean stability</span>
              <b>honest trade-off</b>
            </div>
            <div className="stability-values">
              <div>
                <span>Nominal</span>
                <strong>0.90338</strong>
              </div>
              <div>
                <span>GuardianSim</span>
                <strong>0.89731</strong>
              </div>
            </div>
            <p>−0.00607 while preserving 20/20 success.</p>
          </article>
        </div>

        <div className="evidence-lower">
          <article className="selection-card">
            <div className="card-heading">
              <div>
                <span>Selected actions</span>
                <h3>20 independent executions</h3>
              </div>
              <b>1 nominal fallback</b>
            </div>
            <div className="selection-rows">
              {selectionRows.map((row) => (
                <div className="selection-row" key={row.label}>
                  <span>{row.label}</span>
                  <div>
                    <i
                      className={`tone-${row.tone}`}
                      style={{ width: `${row.count * 10}%` }}
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
                <span>Recovered failure seeds</span>
                <h3>104 · 107 · 120</h3>
              </div>
              <b>3/3 succeeded</b>
            </div>
            <div className="seed-table" role="table" aria-label="Recovered failure seeds">
              {failureSeeds.map((row) => (
                <div role="row" className="seed-row" key={row.seed}>
                  <strong role="cell">{row.seed}</strong>
                  <span role="cell">{row.candidate}</span>
                  <span role="cell">S {row.stability}</span>
                  <span role="cell">C {row.clearance}</span>
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
        </div>
        <div className="architecture-grid">
          {[
            ["01", "Snapshot", "Capture Franka qpos, YCB poses and a stable SHA-256 fingerprint."],
            ["02", "Counterfactuals", "Restore the same state and execute 15 candidate grasp-and-lift trials."],
            ["03", "Two-channel risk", "Separate intentional support contact from non-support clutter clearance."],
            ["04", "Robust selection", "Confirm likely actions, aggregate worst observations and fall back when marginal."],
            ["05", "Independent replay", "Execute nominal and GuardianSim actions independently from the episode snapshot."],
          ].map(([number, title, body]) => (
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
          <a href="/evidence/gate-2-8-report.json" download>
            Download schema-3 report <span>↓</span>
          </a>
          <a href="/evidence/gate-2-8-terminal.png" target="_blank">
            View cloud exit evidence <span>↗</span>
          </a>
          <a
            href="https://github.com/nvm-star-max/GuardianSim"
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
        <span>Evidence frozen · 2026-07-25</span>
      </footer>
    </main>
  );
}
