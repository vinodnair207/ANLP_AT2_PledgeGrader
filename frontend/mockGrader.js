// UI-only mock grader. Produces the same shape of result the backend will
// eventually return, so ResultView doesn't need to change when api.py is wired in.
//
// Result shape:
// {
//   score: 0-100,
//   kind: "Net zero" | "Reduction target" | "No target",
//   summary: string,
//   checks: [{ id, name, tag, found, evidence, start, end, tip }],
//   methods: [{ id, name, time, label, detail?, confidence?, quote? }],
// }

const CHECK_META = {
  year: {
    name: "Target year",
    tag: "TARGET YEAR",
    foundPhrase: "names a year",
    missingPhrase: "names no target year",
    tip: "A stronger pledge names the year it will reach its target, e.g. by 2040.",
  },
  scope3: {
    name: "Scope 3",
    tag: "SCOPE 3",
    foundPhrase: "covers the whole supply chain",
    missingPhrase: "leaves out suppliers' and customers' emissions",
    tip: "A stronger pledge covers suppliers' and customers' emissions (Scope 3), not just its own operations.",
  },
  offsets: {
    name: "Offsets",
    tag: "OFFSETS",
    foundPhrase: "explains how offsets are used",
    missingPhrase: "doesn't say how offsets will be used",
    tip: "A stronger pledge says how much it relies on offsets or carbon removal, and what kind.",
  },
  milestones: {
    name: "Interim milestones",
    tag: "MILESTONE",
    foundPhrase: "sets an interim milestone",
    missingPhrase: "sets no interim milestones",
    tip: "A stronger pledge sets a nearer target on the way, e.g. a 50% cut by 2030.",
  },
};

const ORDER = ["year", "scope3", "offsets", "milestones"];

function findAll(regex, text) {
  const out = [];
  const re = new RegExp(regex.source, regex.flags.includes("g") ? regex.flags : regex.flags + "g");
  let m;
  while ((m = re.exec(text))) out.push({ text: m[0], start: m.index, end: m.index + m[0].length, year: m[1] });
  return out;
}

function detectSpans(text) {
  const years = findAll(/\b(?:by|in|before|until)\s+(20\d\d)\b/i, text);
  const target = years.length ? years.reduce((a, b) => (Number(b.year) > Number(a.year) ? b : a)) : null;

  let milestone = findAll(/\b\d{1,3}\s?%\s*(?:cut|reduction|decrease|lower)?[^.,;]*?\bby\s+20\d\d\b/i, text)
    .find((m) => !target || m.end <= target.start || m.start >= target.end);
  if (!milestone && years.length > 1) milestone = years.find((y) => y !== target);

  const scope3 = findAll(
    /\b(?:including |across |covering )?scopes?\s*(?:1,?\s*2,?\s*(?:and|&)\s*)?3(?:\s+emissions)?\b|\b(?:supply|value) chain\b/i,
    text
  )[0];

  const offsets = findAll(/\b(?:verified |high-quality )?(?:offsets?|carbon removals?|carbon credits?)\b/i, text)[0];

  return { year: target, scope3, offsets, milestones: milestone };
}

function joinPhrases(list, word = "and") {
  if (list.length <= 1) return list.join("");
  return `${list.slice(0, -1).join(", ")} ${word} ${list[list.length - 1]}`;
}

function verdictFor(score) {
  if (score === 100) return "Strong";
  if (score === 75) return "Mostly supported";
  if (score === 50) return "Half supported";
  if (score === 25) return "Weakly supported";
  return "Headline only";
}

function kindOf(text) {
  if (/net[\s-]?zero|carbon neutral/i.test(text)) return "Net zero";
  if (/\b(reduc\w*|cut\w*|lower\w*)\b/i.test(text) && /\d/.test(text)) return "Reduction target";
  return "No target";
}

export function mockGrade(text) {
  const spans = detectSpans(text);

  const checks = ORDER.map((id) => {
    const span = spans[id];
    return {
      id,
      ...CHECK_META[id],
      found: Boolean(span),
      evidence: span ? span.text : null,
      start: span ? span.start : null,
      end: span ? span.end : null,
    };
  });

  const found = checks.filter((c) => c.found);
  const missing = checks.filter((c) => !c.found);
  const score = found.length * 25;
  const kind = kindOf(text);

  let summary = `${verdictFor(score)}.`;
  if (found.length && missing.length) {
    summary += ` It ${joinPhrases(found.map((c) => c.foundPhrase))}, but it ${joinPhrases(missing.map((c) => c.missingPhrase))}.`;
  } else if (found.length) {
    summary += ` It ${joinPhrases(found.map((c) => c.foundPhrase))}.`;
  } else {
    summary += ` It ${joinPhrases(missing.map((c) => c.missingPhrase))}.`;
  }

  const shortMissing = missing.map((c) => ({ year: "a target year", scope3: "Scope 3", offsets: "offsets", milestones: "interim steps" })[c.id]);
  let quote;
  if (kind === "No target") {
    quote = "No measurable target; this reads as a general statement of intent.";
  } else {
    quote = `A ${spans.year ? "dated" : "undated"} ${kind.toLowerCase()} target`;
    if (spans.scope3) quote += " that covers Scope 3";
    quote += shortMissing.length ? `, with no detail on ${joinPhrases(shortMissing, "or")}.` : ", with detail on offsets and interim steps.";
  }

  const methods = [
    {
      id: "rules",
      name: "Rule-based",
      time: "4 ms",
      label: kind,
      detail:
        kind === "No target"
          ? "No target keywords matched. No confidence score: rules either match or don't."
          : `Matched “${kind.toLowerCase()}”${spans.year ? " and a year" : ""}. No confidence score: rules either match or don't.`,
    },
    { id: "climatebert", name: "ClimateBERT", time: "0.12 s", label: kind, confidence: 93 },
    { id: "llm", name: "Zero-shot LLM", time: "4.8 s", label: kind, quote },
  ];

  return { score, kind, summary, checks, methods };
}
