import { useEffect, useState } from "react";
import ResultView from "./ResultView.jsx";
import sampleResult from "./sampleResult.json";

const MIN_CHARS = 20;
const MAX_CHARS = 2000;

// Invented examples for illustration only (not real companies).
const EXAMPLES = [
  {
    name: "Strong pledge",
    text: "We will reach net zero across Scopes 1, 2 and 3 by 2040, with a 50% cut in absolute emissions by 2030 against a 2020 baseline. Offsets will only be used for residual emissions, through verified carbon removals.",
  },
  {
    name: "Half supported",
    text: "We aim to be net zero in our own operations by 2035, cutting emissions by 30% by 2028. We are still assessing emissions from our supply chain.",
  },
  {
    name: "Headline only",
    text: "We are committed to becoming a net-zero business and to playing our part in the fight against climate change.",
  },
  {
    name: "Reduction target",
    text: "We will reduce our Scope 1 and 2 emissions by 40% by 2030 compared with 2019 levels.",
  },
  {
    name: "No target",
    text: "Sustainability is at the heart of everything we do, and we care deeply about the planet and our communities.",
  },
];

const CHECKS = [
  { title: "Target year", text: "Does the pledge name a specific year?" },
  { title: "Scope 3", text: "Does it cover suppliers' and customers' emissions?" },
  { title: "Offsets", text: "Does it explain how offsets or removals are used?" },
  { title: "Interim milestones", text: "Are there smaller targets on the way?" },
];

const NAV = ["Grade a pledge", "How scoring works", "Method comparison"];

// UI-only mock: each method "finishes" after `delay` ms with a fake result.
// Replace with real API calls later.
const MOCK_METHODS = [
  { id: "rules", name: "Rule-based", delay: 600, time: "4 ms", result: "Net zero", hint: "Usually instant" },
  { id: "climatebert", name: "ClimateBERT", delay: 1500, time: "0.1 s", result: "Net zero · 93%", hint: "Usually under 1 second" },
  { id: "llm", name: "Zero-shot LLM", delay: 5000, time: "4.2 s", result: "Net zero", hint: "Usually 3–8 seconds" },
];

function Logo() {
  return (
    <svg width="34" height="34" viewBox="0 0 34 34" aria-hidden="true">
      <circle cx="17" cy="17" r="16" fill="#f3f0e8" />
      <path d="M8 21 A9 9 0 0 1 12.5 13.2" stroke="#2f8f5b" strokeWidth="3" fill="none" strokeLinecap="round" />
      <path d="M13.8 12.5 A9 9 0 0 1 20.2 12.5" stroke="#e6b422" strokeWidth="3" fill="none" strokeLinecap="round" />
      <path d="M21.5 13.2 A9 9 0 0 1 26 21" stroke="#f28c1e" strokeWidth="3" fill="none" strokeLinecap="round" />
      <line x1="17" y1="21" x2="22" y2="15" stroke="#0f3b2e" strokeWidth="2.2" strokeLinecap="round" />
      <circle cx="17" cy="21" r="2" fill="#0f3b2e" />
    </svg>
  );
}

function Spinner({ size = 16 }) {
  return <span className="spinner" style={{ width: size, height: size }} aria-hidden="true" />;
}

function CheckIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
      <circle cx="8" cy="8" r="8" fill="#1d5a45" />
      <path d="M4.5 8.2 L7 10.5 L11.5 5.8" stroke="#fff" strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Header({ active, onNavigate }) {
  return (
    <header className="header">
      <div className="container header-inner">
        <a className="brand" href="/">
          <Logo />
          PledgeGrader
        </a>
        <nav className="nav">
          {NAV.map((item) => (
            <button
              key={item}
              className={`nav-link ${active === item ? "active" : ""}`}
              onClick={() => onNavigate(item)}
            >
              {item}
            </button>
          ))}
        </nav>
      </div>
    </header>
  );
}

/* ---------------- Input view ---------------- */

function PledgeForm({ text, setText, onGrade }) {
  const [example, setExample] = useState(null);

  const length = text.length;
  const valid = length >= MIN_CHARS && length <= MAX_CHARS;

  function clear() {
    setText("");
    setExample(null);
  }

  return (
    <section className="card">
      <span className="label">New here? Try an example</span>
      <div className="chips">
        {EXAMPLES.map((ex) => (
          <button
            key={ex.name}
            className={`chip ${example === ex.name ? "active" : ""}`}
            onClick={() => {
              setExample(ex.name);
              setText(ex.text);
            }}
          >
            {ex.name}
          </button>
        ))}
      </div>
      <p className="hint">
        Examples are invented for illustration and are not real companies. Picking one fills the box below.
      </p>

      <div className="field">
        <label className="label" htmlFor="pledge">Pledge text</label>
        <textarea
          id="pledge"
          value={text}
          maxLength={MAX_CHARS}
          onChange={(e) => {
            setText(e.target.value);
            setExample(null);
          }}
          placeholder="e.g. We will reach net zero across Scopes 1, 2 and 3 by 2040, with a 50% cut by 2030."
        />
        <div className="field-meta hint">
          <span>One sentence to a short paragraph · English · 20–2,000 characters</span>
          <span>{length.toLocaleString()} / 2,000</span>
        </div>
      </div>

      <div className="actions">
        <button className="btn-primary" onClick={onGrade} disabled={!valid}>
          Grade pledge
        </button>
        <button className="btn-secondary" onClick={clear}>Clear</button>
        <span className="hint">Takes about 5–10 seconds</span>
      </div>
    </section>
  );
}

function WhatGetsChecked() {
  return (
    <section className="checks">
      <h2>What gets checked</h2>
      <div className="check-grid">
        {CHECKS.map((c) => (
          <div key={c.title} className="check-card">
            <div className="points">+25 POINTS</div>
            <h3>{c.title}</h3>
            <p>{c.text}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function InputView({ text, setText, onGrade }) {
  return (
    <>
      <section className="hero">
        <p className="eyebrow">FREE · EXPLAINABLE · INSTANT</p>
        <h1>How solid is this net-zero pledge?</h1>
        <p>
          Paste a sentence or paragraph from a company's climate pledge. PledgeGrader checks it for four
          signs of a believable plan and shows how three NLP methods read it.
        </p>
      </section>
      <PledgeForm text={text} setText={setText} onGrade={onGrade} />
      <WhatGetsChecked />
      <footer className="footer">
        <span>A first check, not a final verdict. Verify anything important with an expert.</span>
        <span>36118 Applied NLP · Group 14 · UTS</span>
      </footer>
    </>
  );
}

/* ---------------- Loading view ---------------- */

function MethodCard({ method, done }) {
  return (
    <div className={`method-card ${done ? "" : "pending"}`}>
      <div className="method-head">
        <h3>{method.name}</h3>
        {done ? (
          <span className="status done"><CheckIcon /> Done · {method.time}</span>
        ) : (
          <span className="status reading"><Spinner size={14} /> Reading...</span>
        )}
      </div>
      {done ? (
        <span className="pill">{method.result}</span>
      ) : (
        <>
          <span className="pill-skeleton shimmer" />
          <p className="method-hint">{method.hint}</p>
        </>
      )}
    </div>
  );
}

function LoadingView({ text, onDone }) {
  const [doneIds, setDoneIds] = useState([]);

  useEffect(() => {
    const timers = MOCK_METHODS.map((m) =>
      setTimeout(() => setDoneIds((prev) => [...prev, m.id]), m.delay)
    );
    return () => timers.forEach(clearTimeout);
  }, []);

  const doneCount = doneIds.length;
  const total = MOCK_METHODS.length;

  // Short pause once all methods finish, so the full progress bar is visible.
  useEffect(() => {
    if (doneCount !== total) return;
    const t = setTimeout(onDone, 600);
    return () => clearTimeout(t);
  }, [doneCount, total, onDone]);

  return (
    <div className="loading-page">
      <section className="card">
        <span className="label">Your pledge</span>
        <div className="pledge-readonly">{text}</div>
        <div className="actions">
          <button className="btn-primary grading" disabled>
            <Spinner size={18} /> Grading...
          </button>
          <span className="hint">Text box and examples are locked until grading finishes.</span>
        </div>
      </section>

      <section className="progress-section">
        <div className="progress-head">
          <h2>Grading your pledge...</h2>
          <span className="progress-count">{doneCount} of {total} methods done</span>
        </div>
        <div className="progress-track" role="progressbar" aria-valuenow={doneCount} aria-valuemin={0} aria-valuemax={total}>
          <div className="progress-fill" style={{ width: `${(doneCount / total) * 100}%` }} />
        </div>
      </section>

      <section className="score-skeleton">
        <div className="score-left">
          <span className="sk sk-eyebrow" />
          <span className="sk sk-score" />
          <div className="sk-segments">
            <span className="sk" />
            <span className="sk" />
            <span className="sk" />
            <span className="sk" />
          </div>
        </div>
        <div className="score-right">
          <span className="sk sk-line" style={{ width: "100%" }} />
          <span className="sk sk-line" style={{ width: "92%" }} />
          <span className="sk sk-line" style={{ width: "60%" }} />
          <p>Score and explanation appear once all three methods have answered (or after 15 s).</p>
        </div>
      </section>

      <section className="methods">
        <h2>How the three methods read it</h2>
        <div className="method-grid">
          {MOCK_METHODS.map((m) => (
            <MethodCard key={m.id} method={m} done={doneIds.includes(m.id)} />
          ))}
        </div>
      </section>
    </div>
  );
}

/* ---------------- App ---------------- */

export default function App() {
  const [page, setPage] = useState("Grade a pledge");
  const [view, setView] = useState("input"); // "input" | "loading" | "result"
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);

  function grade() {
    // UI-only for now: always shows the sample JSON. Later, replace with the
    // JSON returned by api.py for this text.
    setResult(sampleResult);
    setView("loading");
  }

  function gradeAnother() {
    setText("");
    setResult(null);
    setView("input");
    window.scrollTo(0, 0);
  }

  return (
    <>
      <Header active={page} onNavigate={setPage} />
      <main className="container">
        {view === "input" && <InputView text={text} setText={setText} onGrade={grade} />}
        {view === "loading" && <LoadingView text={text} onDone={() => setView("result")} />}
        {view === "result" && (
          <ResultView text={result.text} result={result} onGradeAnother={gradeAnother} onNavigate={setPage} />
        )}
      </main>
    </>
  );
}
