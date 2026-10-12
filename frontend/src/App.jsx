import { useEffect, useState } from "react";
import ResultView from "./ResultView.jsx";

const MIN_CHARS = 20;
const MAX_CHARS = 2000;
const STEP_SECONDS = 1; // each method card shows "Reading..." for this long, one after another

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

const NAV 
  = 
    [
      "Grade a pledge", 
      // "How scoring works", 
      // "Method comparison"
    ];

// Display info for each method card before its result arrives.
const METHODS = [
  { id: "rules", name: "Rule-based", hint: "Usually instant" },
  { id: "climatebert", name: "ClimateBERT", hint: "Usually under 1 second" },
  { id: "llm", name: "Zero-shot LLM", hint: "Usually 1-5 seconds" },
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

function PledgeForm({ text, setText, onGrade, error, setError }) {
  const [example, setExample] = useState(null);

  const length = text.length;
  const valid = length >= MIN_CHARS && length <= MAX_CHARS;

  function clear() {
    setText("");
    setExample(null);
    setError("");
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
              setError("");
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
            setError(""); 
          }}
          placeholder="e.g. We will reach net zero across Scopes 1, 2 and 3 by 2040, with a 50% cut by 2030."
        />
        <div className="field-meta hint">
          <span>One sentence to a short paragraph · English · 20–2,000 characters</span>
          <span>{length.toLocaleString()} / 2,000</span>
        </div>
        {error && <p className="field-error" role="alert">{error}</p>}
      </div>

      <div className="actions">
        <button className="btn-primary" onClick={onGrade} disabled={!valid}>
          Grade Pledge
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

function InputView({ text, setText, onGrade, error, setError }) {
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
      <PledgeForm text={text} setText={setText} onGrade={onGrade} error={error} setError={setError} />
      <WhatGetsChecked />
      <footer className="footer">
        <span>A first check, not a final verdict. Verify anything important with an expert.</span>
        <span>36118 Applied NLP · Group 14 · UTS</span>
      </footer>
    </>
  );
}

/* ---------------- Loading view ---------------- */

function MethodCard({ method, result }) {
  const done = Boolean(result);
  const failed = done && !result.label;
  return (
    <div className={`method-card ${done ? "" : "pending"}`}>
      <div className="method-head">
        <h3>{method.name}</h3>
        {done ? (
          <span className="status done"><CheckIcon /> Done · {result.time}</span>
        ) : (
          <span className="status reading"><Spinner size={14} /> Reading...</span>
        )}
      </div>
      {done ? (
        <span className="pill">
          {failed ? "Unavailable" : result.label}
          {result.confidence != null && ` · ${result.confidence}%`}
        </span>
      ) : (
        <>
          <span className="pill-skeleton shimmer" />
          <p className="method-hint">{method.hint}</p>
        </>
      )}
    </div>
  );
}

function LoadingView({ text, result, onDone }) {
  // Stopwatch from the moment the loading screen appears.
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    const start = Date.now();
    const timer = setInterval(() => setElapsed((Date.now() - start) / 1000), 100);
    return () => clearInterval(timer);
  }, []);

  // Cards are revealed one per STEP_SECONDS, in order (rules -> ClimateBERT -> LLM),
  // but never before the response has arrived. The card itself shows the real data.
  let revealAt = 0;
  const cards = METHODS.map((m) => {
    const data = result
      ? result.methods.find((r) => r.id === m.id) || { id: m.id, label: null, time: "n/a" }
      : null;
    revealAt += STEP_SECONDS;
    return { method: m, data, revealed: Boolean(data) && elapsed >= revealAt };
  });

  const doneCount = cards.filter((c) => c.revealed).length;
  const total = METHODS.length;
  const allDone = doneCount === total;

  // Once every card is revealed, pause briefly, then show the result page.
  useEffect(() => {
    if (!allDone) return;
    const t = setTimeout(onDone, 800);
    return () => clearTimeout(t);
  }, [allDone, onDone]);

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
          <span className="progress-count">
            {doneCount} of {total} methods done · {elapsed.toFixed(1)} s
          </span>
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
          {cards.map((c) => (
            <MethodCard key={c.method.id} method={c.method} result={c.revealed ? c.data : null} />
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
  const [error, setError] = useState(""); // message shown under the text box

  async function grade() {
    setResult(null);
    setError("");
    setView("loading"); // show the loading screen straight away

    try {
      const res = await fetch("/api/grade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text }),
      });
      const data = await res.json();

      if (!res.ok) {
        // e.g. 400 from validate_text: {"detail": "Please enter at least 20 characters."}
        setError(data.detail || "Something went wrong. Please try again.");
        setView("input");
        return;
      }

      setResult(data); // LoadingView sees this, fills the cards, then moves to the result page
    } catch (err) {
      console.error("Couldn't reach the grader:", err);
      setError("Couldn't reach the grader. Is the backend running on port 8000?");
      setView("input");
    }
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
        {view === "input" && (
          <InputView text={text} setText={setText} onGrade={grade} error={error} setError={setError} />
        )}
        {view === "loading" && <LoadingView text={text} result={result} onDone={() => setView("result")} />}
        {view === "result" && (
          <ResultView text={result.text} result={result} onGradeAnother={gradeAnother} onNavigate={setPage} />
        )}
      </main>
    </>
  );
}
