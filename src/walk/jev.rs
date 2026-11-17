//! JEV: the decision model as a door decider. Its one job is to rank a wave's batch of doors; the question reaches
//! it here and nowhere else (Sirsh, 17 Nov 2026). This is the walk's only door to the model: `doors.rs` and `lab.rs`
//! never call it (tests/doors.rs), and the labeller that writes a door's text has no question argument.
//!
//! A wave is asked exactly as the lab asks it (p8-subsystems `meta/lab/walklab/jevcache.py`, `knowable.JevDecider`,
//! measured in #837 to rank better than BM25 and word overlap on NDCG@10):
//!   requests  the wave's doors in key order (en_US collation), cut into requests of at most 60 options and 24,000
//!             bytes of (text + key + 64)
//!   request   {"model", "state": {"question", "task"[, "found"]}, "questions": {"c<j>": {"type": "noul",
//!             "instructions": <door text>}}}, the bytes `httpx` sends for the lab (compact, UTF-8 unescaped)
//!   batched   a wave's requests go together, at most 16 in flight; each answer is recorded in decisions.jsonl under
//!             the sha256 of its bytes and replayed from there
//!   merge     every door by Jev's raw P(yes) across requests, ties by key under the walk's collation
//!   kappa     with a kappa hook, the walk's past (K6: an opening sentence per read, `walk::kappa`) goes in the state as
//!             `found`, as the lab's kappa round 3 asked; an empty past adds no `found`, as the lab's `if f:` does
//!   keys      F2 by default (`{j}_{slug of the door's head}`, `ceiling.present("F2")`, what D6 and K6 were measured
//!             with); `c{j}` (jevcache) for parity
//! A door's text is its labeller's `immediate`, joined by newlines. The question is in the state and nowhere else.

use std::collections::BTreeMap;

use serde::Serialize;

use super::doors::{by_score, Batch, Decider, Ranked};
use super::lab::{collate, Read};
use crate::infer::Model;
use crate::Result;

/// jevcache.TASK_LINES, word for word.
pub const TASK_LINES: &str = "For each option, a lead to messages in the user's earlier conversations that have not been read yet, described by what the user said in them and where they sit. Would following it likely reach information needed to answer `question`, or part of it?";
/// Dollars per input token (jevcache.PRICE_IN).
pub const PRICE_IN: f64 = 0.042 / 1e6;
pub const MAX_OPTIONS: usize = 60;
pub const LIMIT_BYTES: usize = 24000;

/// jevcache.requests: the doors' keys in collation order, cut by count and by cumulative bytes.
pub fn requests(texts: &BTreeMap<String, String>) -> Vec<Vec<String>> {
    let mut keys: Vec<&String> = texts.keys().collect();
    keys.sort_by_key(|k| collate(k));
    let mut out: BTreeMap<(usize, usize), Vec<String>> = BTreeMap::new();
    let mut cum = 0usize;
    for (i, k) in keys.into_iter().enumerate() {
        cum += texts[k].len() + k.len() + 64;
        out.entry((cum / LIMIT_BYTES, i / MAX_OPTIONS)).or_default().push(k.clone());
    }
    out.into_values().collect()
}

fn js(s: &str) -> String {
    serde_json::to_string(s).expect("a string serialises")
}

/// How a request names its options. `F2` is what D6 (+.061) and K6 (+.046) were measured with (the lab's
/// `ceiling.present("F2")`): `{j}_{slug of the door's head}`. `C` is `c{j}`, the lab's jevcache, kept for parity.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Keys {
    F2,
    C,
}

impl std::str::FromStr for Keys {
    type Err = String;
    fn from_str(s: &str) -> std::result::Result<Keys, String> {
        match s {
            "f2" | "F2" => Ok(Keys::F2),
            "c" | "C" => Ok(Keys::C),
            _ => Err(format!("keys is f2 or c, not {s}")),
        }
    }
}

fn py_space(c: char) -> bool {
    c.is_whitespace() || ('\x1c'..='\x1f').contains(&c)
}

fn digits(s: &str) -> (&str, &str) {
    let n = s.find(|c: char| !c.is_ascii_digit()).unwrap_or(s.len());
    (&s[..n], &s[n..])
}

/// ceiling.TERM: `the term 'X', held by N message(s) in all, U of them unread. ` → (X, U).
fn term_head(text: &str) -> Option<(&str, &str)> {
    let rest = text.strip_prefix("the term '")?;
    let q = rest.find('\'')?;
    let (x, rest) = (&rest[..q], rest[q..].strip_prefix("', held by ")?);
    let (n, rest) = digits(rest);
    let rest = rest.strip_prefix(" message(s) in all, ").filter(|_| !n.is_empty())?;
    let (u, rest) = digits(rest);
    rest.strip_prefix(" of them unread. ").filter(|_| !u.is_empty())?;
    Some((x, u))
}

/// One snippet of a describe.lines door, as `compact` reads it: `"line" (where)` becomes `line (where)`.
fn snippet(s: &str) -> String {
    if s.starts_with('"') {
        let ends: Vec<usize> = s.char_indices().filter(|(i, c)| *c == '"' && *i > 0).map(|(i, _)| i).collect();
        for &i in ends.iter().rev() {
            let rest = s[i + 1..].trim_start_matches(py_space);
            let place = rest.is_empty() || ((rest.starts_with("(same sitting") || rest.starts_with("(another sitting")) && rest.ends_with(')'));
            if place {
                let line = s[1..i].trim_matches(py_space);
                return if rest.is_empty() { line.to_string() } else { format!("{line} {rest}") };
            }
        }
    }
    s.trim_matches('"').to_string()
}

/// ceiling.compact (F1/F2's layout) of a describe.lines door: (head, head + one snippet a line).
pub fn compact(text: &str) -> (String, String) {
    let said = ["What the user said in them: ", "by a sentence that names something both mention: "].iter()
        .filter_map(|m| text.find(m).map(|i| (i, i + m.len()))).min();
    let head = match term_head(text) {
        Some((x, u)) => format!("term '{x}' · {u} unread"),
        None => text[..said.map(|s| s.0).unwrap_or(text.len())].trim_matches(py_space).trim_end_matches(['.', ':']).replace("unread message(s)", "unread"),
    };
    let rest = said.map(|s| &text[s.1..]).unwrap_or("");
    let lines: Vec<String> = rest.split(" | ").map(|x| x.trim_matches(py_space)).filter(|x| !x.is_empty()).map(|x| format!("- {}", snippet(x))).collect();
    let body = format!("{head}\n{}", lines.join("\n"));
    (head, body)
}

/// An F2 key: `{j}_{head up to " · "}`, lowercased, every run of other characters one `_`, trimmed, 60 characters.
pub fn f2_key(j: usize, head: &str) -> String {
    let raw = format!("{j}_{}", head.split(" · ").next().unwrap_or("")).to_lowercase();
    let mut out = String::new();
    let mut gap = false;
    for c in raw.chars() {
        if c.is_ascii_lowercase() || c.is_ascii_digit() {
            if gap && !out.is_empty() {
                out.push('_');
            }
            gap = false;
            out.push(c);
        } else {
            gap = true;
        }
    }
    out.chars().take(60).collect()
}

/// An option as a request shows it: (key, text). A describe.lines door is laid out by `compact`, as the lab's F2
/// arm sent it; any other door (D6) keeps its text, and its head is its first line.
pub fn option(keys: Keys, j: usize, text: &str, describe_lines: bool) -> (String, String) {
    match keys {
        Keys::C => (format!("c{j}"), text.to_string()),
        Keys::F2 if describe_lines => {
            let (head, body) = compact(text);
            (f2_key(j, &head), body)
        }
        Keys::F2 => {
            let first = text.lines().next().unwrap_or("");
            let head = first.trim_matches(py_space).trim_end_matches(['.', ':']).replace("unread message(s)", "unread");
            (f2_key(j, &head), text.to_string())
        }
    }
}

/// One request's bytes, keys in the order the lab's client writes them.
pub fn body(model: &str, question: &str, task: &str, found: Option<&[String]>, options: &[(String, String)]) -> String {
    let mut s = format!("{{\"model\":{},\"state\":{{\"question\":{},\"task\":{}", js(model), js(question), js(task));
    if let Some(f) = found {
        s += &format!(",\"found\":{}", serde_json::to_string(f).expect("strings serialise"));
    }
    s += "},\"questions\":{";
    for (j, (k, t)) in options.iter().enumerate() {
        if j > 0 {
            s.push(',');
        }
        s += &format!("{}:{{\"type\":\"noul\",\"instructions\":{}}}", js(k), js(t));
    }
    s + "}}"
}

/// What one wave cost.
#[derive(Clone, Debug, Default, Serialize)]
pub struct WaveCost {
    pub wave: u32,
    pub doors: usize,
    pub requests: usize,
    pub replayed: usize,
    pub called: usize,
    /// Input tokens of the requests sent this time (replayed ones cost nothing).
    pub input_tokens: u64,
    pub cost_usd: f64,
}

/// The walk's past as `found`, from the reads before a wave (never the question).
pub type Kappa<'m> = Box<dyn FnMut(&[Read]) -> Result<Vec<String>> + 'm>;

/// Jev as a Decider: one batched ask per wave, merged by raw P.
pub struct JevDecider<'m> {
    pub model: &'m mut Model,
    pub task: String,
    /// Builds `found` from the reads so far; none leaves it out of the state.
    pub kappa: Option<Kappa<'m>>,
    /// How options are named: F2 (the default, as measured) or c{j}.
    pub keys: Keys,
    pub waves: Vec<WaveCost>,
}

impl<'m> JevDecider<'m> {
    pub fn new(model: &'m mut Model) -> JevDecider<'m> {
        JevDecider { model, task: TASK_LINES.into(), kappa: None, keys: Keys::F2, waves: vec![] }
    }

    /// `found` for a wave: the kappa hook's lines on the reads so far, none when there is no hook or no line.
    pub fn found(&mut self, b: &Batch) -> Result<Option<Vec<String>>> {
        match &mut self.kappa {
            Some(k) => Ok(Some(k(b.reads)?).filter(|f| !f.is_empty())),
            None => Ok(None),
        }
    }

    /// One wave's requests: each one's door keys, option keys and bytes. What `rank` sends.
    pub fn requests(&self, b: &Batch, found: Option<&[String]>) -> Vec<(Vec<String>, Vec<String>, String)> {
        let texts: BTreeMap<String, String> = b.doors.keys().map(|k| (k.clone(), b.attrs.get(k).map(|a| a.immediate.join("\n")).unwrap_or_default())).collect();
        let describe_lines = b.label_version.starts_with("describe-lines");
        requests(&texts).into_iter().map(|ks| {
            let opts: Vec<(String, String)> = ks.iter().enumerate().map(|(j, k)| option(self.keys, j, &texts[k], describe_lines)).collect();
            let body = body(self.model.name(), b.question, &self.task, found, &opts);
            (ks, opts.into_iter().map(|(k, _)| k).collect(), body)
        }).collect()
    }

    /// One wave's request bodies, with the door keys of each.
    pub fn bodies(&self, b: &Batch, found: Option<&[String]>) -> Vec<(Vec<String>, String)> {
        self.requests(b, found).into_iter().map(|(ks, _, body)| (ks, body)).collect()
    }
}

impl Decider for JevDecider<'_> {
    fn name(&self) -> String {
        format!("jev ({})", self.model.name())
    }
    fn rank(&mut self, b: &Batch) -> Result<Vec<Ranked>> {
        let found = self.found(b)?;
        let reqs = self.requests(b, found.as_deref());
        let bodies: Vec<String> = reqs.iter().map(|(_, _, b)| b.clone()).collect();
        let answers = self.model.ask_bodies(&bodies)?.ok_or("a Jev request is not recorded and there is no key to send it with")?;
        let mut cost = WaveCost { wave: b.wave, doors: b.doors.len(), requests: reqs.len(), ..WaveCost::default() };
        let mut scores = vec![];
        for ((keys, opts, _), a) in reqs.iter().zip(&answers) {
            for (k, o) in keys.iter().zip(opts) {
                let x = &a.response["answers"][o.as_str()];
                let p = x["noul"].as_f64().ok_or_else(|| format!("Jev gave no P for option {o} ({k})"))?;
                scores.push((k.clone(), p));
            }
            if a.replayed {
                cost.replayed += 1;
            } else {
                cost.called += 1;
                let tokens = a.response["usage"]["input_tokens"].as_u64().unwrap_or(0);
                cost.input_tokens += tokens;
                cost.cost_usd += tokens as f64 * PRICE_IN;
            }
        }
        self.waves.push(cost);
        Ok(by_score(scores))
    }
}

/// kappa_state.relations (p8-subsystems `meta/lab/worlds/kappa_state.py`, round 3's K6) over texts the caller holds:
/// the opening sentence of each read (to the first `.`, `!` or `?` followed by whitespace or the end), cut at
/// `cap_each` characters; reads taken through a door first, then the rest; most recent first when `recent_last`;
/// stop before `cap_all` characters. `via[i]` is the read's door, `search…` or none.
pub fn relations(texts: &[String], via: &[Option<String>], cap_each: usize, cap_all: usize, recent_last: bool, door_first: bool) -> Vec<String> {
    let order: Vec<usize> = if recent_last { (0..texts.len()).rev().collect() } else { (0..texts.len()).collect() };
    let is_door = |i: usize| door_first && via.get(i).and_then(|v| v.as_deref()).is_some_and(|v| !v.is_empty() && !v.starts_with("search"));
    let door: Vec<usize> = order.iter().copied().filter(|&i| is_door(i)).collect();
    let rest: Vec<usize> = order.iter().copied().filter(|&i| !is_door(i)).collect();
    let (mut out, mut used) = (vec![], 0usize);
    for i in door.into_iter().chain(rest) {
        let t = texts[i].trim_matches(|c: char| c.is_whitespace() || ('\x1c'..='\x1f').contains(&c));
        let cs: Vec<char> = t.chars().collect();
        let end = (0..cs.len()).find(|&j| matches!(cs[j], '.' | '!' | '?') && cs.get(j + 1).is_none_or(|c| c.is_whitespace() || ('\x1c'..='\x1f').contains(c)));
        let s: String = cs[..end.map(|j| j + 1).unwrap_or(cs.len())].iter().take(cap_each).collect();
        let n = s.chars().count();
        if used + n > cap_all {
            break;
        }
        out.push(s);
        used += n;
    }
    out
}
