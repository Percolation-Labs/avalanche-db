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

/// One request's bytes, keys in the order the lab's client writes them.
pub fn body(model: &str, question: &str, task: &str, found: Option<&[String]>, texts: &[&str]) -> String {
    let mut s = format!("{{\"model\":{},\"state\":{{\"question\":{},\"task\":{}", js(model), js(question), js(task));
    if let Some(f) = found {
        s += &format!(",\"found\":{}", serde_json::to_string(f).expect("strings serialise"));
    }
    s += "},\"questions\":{";
    for (j, t) in texts.iter().enumerate() {
        if j > 0 {
            s.push(',');
        }
        s += &format!("\"c{j}\":{{\"type\":\"noul\",\"instructions\":{}}}", js(t));
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
    pub waves: Vec<WaveCost>,
}

impl<'m> JevDecider<'m> {
    pub fn new(model: &'m mut Model) -> JevDecider<'m> {
        JevDecider { model, task: TASK_LINES.into(), kappa: None, waves: vec![] }
    }

    /// `found` for a wave: the kappa hook's lines on the reads so far, none when there is no hook or no line.
    pub fn found(&mut self, b: &Batch) -> Result<Option<Vec<String>>> {
        match &mut self.kappa {
            Some(k) => Ok(Some(k(b.reads)?).filter(|f| !f.is_empty())),
            None => Ok(None),
        }
    }

    /// One wave's request bodies, with the door keys of each: what `rank` sends.
    pub fn bodies(&self, b: &Batch, found: Option<&[String]>) -> Vec<(Vec<String>, String)> {
        let texts: BTreeMap<String, String> = b.doors.keys().map(|k| (k.clone(), b.attrs.get(k).map(|a| a.immediate.join("\n")).unwrap_or_default())).collect();
        requests(&texts).into_iter().map(|ks| {
            let t: Vec<&str> = ks.iter().map(|k| texts[k].as_str()).collect();
            let body = body(self.model.name(), b.question, &self.task, found, &t);
            (ks, body)
        }).collect()
    }
}

impl Decider for JevDecider<'_> {
    fn name(&self) -> String {
        format!("jev ({})", self.model.name())
    }
    fn rank(&mut self, b: &Batch) -> Result<Vec<Ranked>> {
        let found = self.found(b)?;
        let reqs = self.bodies(b, found.as_deref());
        let bodies: Vec<String> = reqs.iter().map(|(_, b)| b.clone()).collect();
        let answers = self.model.ask_bodies(&bodies)?.ok_or("a Jev request is not recorded and there is no key to send it with")?;
        let mut cost = WaveCost { wave: b.wave, doors: b.doors.len(), requests: reqs.len(), ..WaveCost::default() };
        let mut scores = vec![];
        for ((keys, _), a) in reqs.iter().zip(&answers) {
            for (j, k) in keys.iter().enumerate() {
                let x = &a.response["answers"][format!("c{j}")];
                let p = x["noul"].as_f64().ok_or_else(|| format!("Jev gave no P for option c{j} ({k})"))?;
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
