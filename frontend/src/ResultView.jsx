import { useState } from "react";

function CheckIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" aria-hidden="true">
      <circle cx="8" cy="8" r="8" fill="#1d5a45" />
      <path d="M4.5 8.2 L7 10.5 L11.5 5.8" stroke="#fff" strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function MissingIcon({ size = 20 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" aria-hidden="true">
      <circle cx="10" cy="10" r="8.6" stroke="#b8570f" strokeWidth="1.6" fill="none" />
      <path d="M7 7 L13 13 M13 7 L7 13" stroke="#b8570f" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

function CopyIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
      <rect x="4" y="4" width="8.5" height="8.5" rx="1.5" stroke="currentColor" strokeWidth="1.3" fill="none" />
      <path d="M9.5 2.5 V2 A1 1 0 0 0 8.5 1 H2.5 A1.5 1.5 0 0 0 1 2.5 V8.5 A1 1 0 0 0 2 9.5 H2.5" stroke="currentColor" strokeWidth="1.3" fill="none" />
    </svg>
  );
}

// Test set results (517 held out sentences), copied from outputs/report/table_results.csv.
const TEST_RESULTS = [
  { name: "Rule-based", accuracy: "0.9226", f1: "0.9137" },
  { name: "ClimateBERT", accuracy: "0.9613", f1: "0.9554" },
  { name: "Zero-shot LLM", accuracy: "0.9497", f1: "0.9426" },
];

// Explains how the score is built from the four checks.
function ScoringExplainer() {
  return (
    <section className="panel explainer" aria-live="polite">
      <h2 className="panel-title">How the score works</h2>
      <p>
        The score is the sum of four checks worth 25 points each: a named target year, Scope 3 coverage, an
        explanation of how offsets are used, and interim milestones. A pledge can therefore score 0, 25, 50, 75 or
        100. If the pledge states no target at all, no check is graded and the score is 0.
      </p>
      <p>
        A check counts only when the wording gives real evidence, such as a year tied to the target, and not just a
        related keyword. The score is always calculated in code from the checks and never by a language model. It
        measures how well a pledge is worded and supported. It does not show whether the company will deliver.
      </p>
    </section>
  );
}

// Shows how each method performed on the shared held out test set.
function CompareExplainer() {
  return (
    <div className="explainer-inline" aria-live="polite">
      <table className="score-table">
        <caption>Target type results on 517 held out test sentences</caption>
        <thead>
          <tr><th>Method</th><th>Accuracy</th><th>Macro F1</th></tr>
        </thead>
        <tbody>
          {TEST_RESULTS.map((r) => (
            <tr key={r.name}><td>{r.name}</td><td>{r.accuracy}</td><td>{r.f1}</td></tr>
          ))}
        </tbody>
      </table>
      <p>
        Both ClimateBERT and the zero-shot LLM beat the rule-based baseline by more than chance would explain. The
        two newer methods cannot be separated statistically (p value 0.31), so a disagreement between them is a
        reason to read the pledge yourself.
      </p>
    </div>
  );
}

const SEGMENT_LABELS = { year: "Year", scope3: "Scope 3", offsets: "Offsets", milestones: "Milestones" };

function ScoreCard({ result, onHowScored, expanded }) {
  return (
    <section className="score-card">
      <div className="score-left">
        <span className="score-eyebrow">ROBUSTNESS SCORE</span>
        <div className="score-number">
          <strong>{result.score}</strong> <span>/ 100</span>
        </div>
        <div className="score-segments">
          {result.checks.map((c) => (
            <div key={c.id} className="segment">
              <span className={`segment-bar ${c.found ? "filled" : ""}`} />
              <span className="segment-label">{SEGMENT_LABELS[c.id]}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="score-right">
        <span className="kind-pill">Kind of promise: {result.kind}</span>
        <p className="score-summary">{result.summary}</p>
        <button className="link-light" onClick={onHowScored} aria-expanded={expanded}>
          How is this scored? 25 points for each check passed.
        </button>
      </div>
    </section>
  );
}

function FourChecks({ checks }) {
  return (
    <section className="panel">
      <h2 className="panel-title">The four checks</h2>
      <ul className="check-list">
        {checks.map((c) => (
          <li key={c.id} className="check-row">
            <span className="check-icon">{c.found ? <CheckIcon size={20} /> : <MissingIcon />}</span>
            <div className="check-body">
              <div className="check-head">
                <strong>{c.name}</strong>
                <span className={c.found ? "found" : "missing"}>{c.found ? "Found · +25" : "Missing · 0"}</span>
              </div>
              <p>{c.found ? <>Evidence: “{c.evidence}”</> : c.tip}</p>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

function EvidencePanel({ text, checks }) {
  const spans = checks
    .filter((c) => c.found)
    .sort((a, b) => a.start - b.start)
    .filter((c, i, arr) => i === 0 || c.start >= arr[i - 1].end); // drop overlaps

  const parts = [];
  let cursor = 0;
  spans.forEach((s) => {
    if (s.start > cursor) parts.push(text.slice(cursor, s.start));
    parts.push(
      <mark key={s.id} className={`hl hl-${s.id}`}>
        {text.slice(s.start, s.end)}
        <sup>{s.tag}</sup>
      </mark>
    );
    cursor = s.end;
  });
  if (cursor < text.length) parts.push(text.slice(cursor));

  const missing = checks.filter((c) => !c.found).map((c) => (c.id === "scope3" ? c.name : c.name.toLowerCase()));
  const missingText = missing.length > 1 ? `${missing.slice(0, -1).join(", ")} or ${missing[missing.length - 1]}` : missing[0];
  const note = missing.length
    ? `Highlights show the words each check matched. Nothing was found for ${missingText}.`
    : "Highlights show the words each check matched.";

  return (
    <section className="panel evidence-panel">
      <h2 className="panel-title">Your pledge, with evidence</h2>
      <p className="evidence-text">{parts}</p>
      <p className="hint">{note}</p>
    </section>
  );
}

function majority(methods) {
  const counts = {};
  methods.forEach((m) => (counts[m.label] = (counts[m.label] || 0) + 1));
  const [label, count] = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
  return { label, count };
}

const NUMBER_WORDS = { 1: "one", 2: "two", 3: "three" };

function MethodResults({ methods, onCompare, expanded }) {
  const { label, count } = majority(methods);
  const allAgree = count === methods.length;

  return (
    <section className="methods">
      <div className="methods-head">
        <h2>How the {NUMBER_WORDS[methods.length] || methods.length} methods read it</h2>
        <span className={`agree-banner ${allAgree ? "" : "split"}`}>
          {allAgree ? <CheckIcon size={14} /> : null}
          {allAgree ? `All ${methods.length} methods agree: ${label}` : `${count} of ${methods.length} agree: ${label}`}
        </span>
      </div>

      <div className="method-grid">
        {methods.map((m) => (
          <div key={m.id} className={`method-card ${!allAgree && m.label !== label ? "odd" : ""}`}>
            <div className="method-head">
              <h3>{m.name}</h3>
              <span className="method-time">{m.time}</span>
            </div>
            <span className="pill">{m.label}</span>
            {m.detail && <p className="method-detail">{m.detail}</p>}
            {m.confidence != null && (
              <div className="confidence">
                <div className="confidence-head">
                  <span>Confidence</span>
                  <strong>{m.confidence}%</strong>
                </div>
                <div className="confidence-track">
                  <div className="confidence-fill" style={{ width: `${m.confidence}%` }} />
                </div>
              </div>
            )}
            {m.quote && <p className="method-detail quote">“{m.quote}”</p>}
          </div>
        ))}
      </div>

      <p className="methods-note">
        When methods disagree, the banner turns orange (“2 of 3 agree”) and the odd one out is outlined, so the
        difference is visible, not hidden.{" "}
        <button className="link" onClick={onCompare} aria-expanded={expanded}>
          {expanded ? "Hide the test set results" : "See how each method scores on our test set"}
        </button>.
      </p>
      {expanded && <CompareExplainer />}
    </section>
  );
}

export default function ResultView({ text, result, onGradeAnother, onNavigate }) {
  const [copied, setCopied] = useState(false);
  const [open, setOpen] = useState(null); // "scoring", "compare" or null
  const toggle = (name) => setOpen((cur) => (cur === name ? null : name));

  async function copyResult() {
    const lines = [
      `PledgeGrader result: ${result.score} / 100 (${result.kind})`,
      result.summary,
      "",
      ...result.checks.map((c) => `${c.found ? "✓" : "✗"} ${c.name}${c.found ? `: “${c.evidence}”` : ""}`),
      "",
      `Pledge: ${text}`,
    ];
    try {
      await navigator.clipboard.writeText(lines.join("\n"));
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* clipboard blocked; ignore */
    }
  }

  return (
    <div className="result-page">
      <div className="result-head">
        <h1>Your result</h1>
        <div className="result-actions">
          <button className="btn-secondary btn-small" onClick={copyResult}>
            <CopyIcon /> {copied ? "Copied!" : "Copy result"}
          </button>
          <button className="btn-primary btn-small" onClick={onGradeAnother}>Grade another pledge</button>
        </div>
      </div>

      <ScoreCard result={result} onHowScored={() => toggle("scoring")} expanded={open === "scoring"} />
      {open === "scoring" && <ScoringExplainer />}

      {result.warnings && result.warnings.length > 0 && (
        <div className="method-warning" role="status">
          {result.warnings.map((w) => (
            <p key={w}>{w}</p>
          ))}
        </div>
      )}

      <div className="result-grid">
        <FourChecks checks={result.checks} />
        <EvidencePanel text={text} checks={result.checks} />
      </div>

      <MethodResults methods={result.methods} onCompare={() => toggle("compare")} expanded={open === "compare"} />

      <footer className="footer">
        <span>A first check, not a final verdict. A high score means the right ingredients are there, not that the company will deliver.</span>
        <span>36118 Applied NLP · Group 14 · UTS</span>
      </footer>
    </div>
  );
}
