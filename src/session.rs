//! A query is a session pinned to a snapshot. Each step pops one node off the reasoning
//! stack, reads its edges with two prefix scans, pushes what is still to visit within
//! the budget, and returns statistics and a continuation token. The agent reasons between
//! steps. Every step is appended to the usage graph in the same log.

use std::collections::BTreeMap;
use std::fmt;
use std::time::Instant;

use serde::{Deserialize, Serialize};

use crate::model::{lit, FactIn, Kind, Pred};
use crate::store::{Dir, Edge, ScanCost, Store};
use crate::Result;

pub const USAGE: &str = "usage";

/// The default walk order: what a node answers and who decided it before how it was built.
/// `parent` is left out so a walk does not slide down commit history; ask for it by name.
pub const DEFAULT_FOLLOW: &[Pred] =
    &[Pred::Answers, Pred::Makes, Pred::Informs, Pred::Mentions, Pred::Cites, Pred::AuthoredBy, Pred::Touches];

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Frame {
    pub node: String,
    pub depth: u32,
    /// How the walk reached it: `<pred> from <node>`.
    pub via: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Session {
    pub id: String,
    pub tenant: u32,
    pub question: String,
    pub snapshot: u64,
    pub budget: usize,
    pub pushed: usize,
    pub step: u32,
    pub stack: Vec<Frame>,
    pub visited: Vec<String>,
}

impl Session {
    pub fn token(&self) -> String {
        format!("{}.{}.{}", self.id, self.step, self.snapshot)
    }
}

pub struct Neighbour {
    pub pred: Pred,
    pub dir: Dir,
    pub node: String,
    pub label: Option<String>,
    pub pushed: bool,
}

pub struct StepOut {
    pub session: Session,
    pub at: Option<Frame>,
    pub label: Option<String>,
    pub attributes: Vec<(Pred, String)>,
    pub neighbours: Vec<Neighbour>,
    pub stats: Stats,
    pub token: Option<String>,
}

#[derive(Default)]
pub struct Stats {
    pub fan_out: usize,
    pub fan_in: usize,
    pub by_pred: BTreeMap<String, usize>,
    pub held_back: usize,
    pub depth: u32,
    pub stack: usize,
    pub budget_left: usize,
    /// Earlier steps, in any session, that visited this node: how worn the path is.
    pub path_use: usize,
    pub keys_read: u64,
    pub micros: u128,
}

fn label(store: &Store, tenant: u32, node: u64, as_of: u64, cost: &mut ScanCost) -> Result<Option<String>> {
    for e in store.edges(tenant, node, Dir::Out, as_of, None, cost)? {
        if e.pred == Pred::Label {
            return Ok(Some(store.name(tenant, e.other)?.trim_start_matches("lit:").to_string()));
        }
    }
    Ok(None)
}

/// Resolve the words of a question to a starting node: the one semantic step on the read
/// path, run once, over question labels only. A typed name (`question:…`) is taken as is.
pub fn resolve(store: &Store, tenant: u32, words: &str) -> Result<String> {
    if Kind::of(words).is_some() {
        return Ok(words.to_string());
    }
    let head = store.head(tenant)?;
    let terms: Vec<String> = words.to_lowercase().split(|c: char| !c.is_alphanumeric()).filter(|w| w.len() > 2).map(String::from).collect();
    let mut best: Option<(usize, String)> = None;
    for (s, o, _) in store.by_pred(tenant, Pred::Label, head, &mut ScanCost::default())? {
        let name = store.name(tenant, s)?;
        if Kind::of(&name) != Some(Kind::Question) {
            continue;
        }
        let text = store.name(tenant, o)?.to_lowercase();
        let score = terms.iter().filter(|t| text.contains(t.as_str())).count();
        if score > 0 && best.as_ref().is_none_or(|(b, _)| score > *b) {
            best = Some((score, name));
        }
    }
    best.map(|(_, n)| n).ok_or_else(|| format!("no question matches {words:?}").into())
}

pub fn ask(store: &Store, tenant: u32, words: &str, budget: usize, as_of: Option<u64>) -> Result<Session> {
    let question = resolve(store, tenant, words)?;
    let head = store.head(tenant)?;
    let session = Session {
        id: format!("s{:x}", std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).map(|d| d.as_nanos() as u64 >> 10).unwrap_or(0)),
        tenant,
        question: question.clone(),
        snapshot: as_of.unwrap_or(head).min(head),
        budget,
        pushed: 1,
        step: 0,
        stack: vec![Frame { node: question.clone(), depth: 0, via: "asked".into() }],
        visited: vec![],
    };
    store.write(tenant, &[FactIn::new(format!("session:{}", session.id), Pred::Asked, question, USAGE)])?;
    store.put_session(&session.id, &serde_json::to_string(&session)?)?;
    Ok(session)
}

pub fn load(store: &Store, token: &str) -> Result<Session> {
    let mut parts = token.split('.');
    let (id, step, snap) = (parts.next().unwrap_or(""), parts.next().and_then(|s| s.parse::<u32>().ok()), parts.next().and_then(|s| s.parse::<u64>().ok()));
    let json = store.get_session(id)?.ok_or_else(|| format!("no session {id}"))?;
    let s: Session = serde_json::from_str(&json)?;
    if step != Some(s.step) || snap != Some(s.snapshot) {
        return Err(format!("stale token {token}: session {id} is at {}", s.token()).into());
    }
    Ok(s)
}

pub fn step(store: &Store, token: &str, follow: &[Pred]) -> Result<StepOut> {
    let started = Instant::now();
    let mut s = load(store, token)?;
    let t = s.tenant;
    let mut cost = ScanCost::default();
    let mut stats = Stats::default();
    let Some(frame) = s.stack.pop() else {
        stats.micros = started.elapsed().as_micros();
        return Ok(StepOut { session: s, at: None, label: None, attributes: vec![], neighbours: vec![], stats, token: None });
    };
    let node = store.id(t, &frame.node)?.ok_or_else(|| format!("{} is not in the store", frame.node))?;
    let usage = store.graph_id(t, USAGE)?;
    let mut edges: Vec<Edge> = store.edges(t, node, Dir::Out, s.snapshot, None, &mut cost)?;
    edges.extend(store.edges(t, node, Dir::In, s.snapshot, None, &mut cost)?);
    edges.retain(|e| Some(e.graph) != usage);
    s.visited.push(frame.node.clone());

    let mut attributes = vec![];
    let mut label_text = None;
    let mut candidates = vec![];
    for e in &edges {
        *stats.by_pred.entry(format!("{}{}", if e.dir == Dir::In { "<-" } else { "" }, e.pred.name())).or_default() += 1;
        if e.dir == Dir::Out {
            stats.fan_out += 1;
        } else {
            stats.fan_in += 1;
        }
        let other = store.name(t, e.other)?;
        if e.pred.is_attribute() {
            let text = other.trim_start_matches("lit:").to_string();
            if e.pred == Pred::Label {
                label_text = Some(text.clone());
            }
            attributes.push((e.pred, text));
        } else if let Some(rank) = follow.iter().position(|p| *p == e.pred) {
            candidates.push((rank, e.pred, e.dir, other));
        }
    }
    // Push lowest priority first so the most wanted edge is on top of the stack.
    candidates.sort_by(|a, b| b.0.cmp(&a.0).then(b.3.cmp(&a.3)));
    let mut neighbours = vec![];
    for (_, pred, dir, other) in candidates {
        let seen = s.visited.contains(&other) || s.stack.iter().any(|f| f.node == other);
        let room = s.pushed < s.budget;
        let pushed = !seen && room;
        if pushed {
            s.stack.push(Frame { node: other.clone(), depth: frame.depth + 1, via: format!("{} {} {}", pred.name(), if dir == Dir::Out { "from" } else { "into" }, frame.node) });
            s.pushed += 1;
        } else if !seen {
            stats.held_back += 1;
        }
        let other_id = store.id(t, &other)?.unwrap();
        neighbours.push(Neighbour { pred, dir, label: label(store, t, other_id, s.snapshot, &mut cost)?, node: other, pushed });
    }
    neighbours.reverse();

    // Path use is read live, not at the snapshot: it is about the store's readers, not its facts.
    let head = store.head(t)?;
    stats.path_use = store.edges(t, node, Dir::In, head, None, &mut cost)?.iter().filter(|e| e.pred == Pred::Visited).count();
    stats.depth = frame.depth;
    stats.stack = s.stack.len();
    stats.budget_left = s.budget.saturating_sub(s.pushed);
    stats.keys_read = cost.keys_read;
    stats.micros = started.elapsed().as_micros();

    s.step += 1;
    let step_node = format!("step:{}-{}", s.id, s.step);
    store.write(
        t,
        &[
            FactIn::new(&step_node, Pred::InSession, format!("session:{}", s.id), USAGE),
            FactIn::new(&step_node, Pred::Visited, &frame.node, USAGE),
            FactIn::new(&step_node, Pred::Returned, lit(&format!("{} edges, {} pushed, {} keys, {}us", edges.len(), neighbours.iter().filter(|n| n.pushed).count(), stats.keys_read, stats.micros)), USAGE),
        ],
    )?;
    store.put_session(&s.id, &serde_json::to_string(&s)?)?;
    let token = if s.stack.is_empty() { None } else { Some(s.token()) };
    Ok(StepOut { session: s, at: Some(frame), label: label_text, attributes, neighbours, stats, token })
}

impl fmt::Display for StepOut {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let Some(at) = &self.at else {
            return writeln!(f, "stack empty: session {} is finished after {} steps", self.session.id, self.session.step);
        };
        writeln!(f, "step {}  {}  (depth {}, reached by {})", self.session.step, at.node, at.depth, at.via)?;
        if let Some(l) = &self.label {
            writeln!(f, "  \"{l}\"")?;
        }
        for (p, v) in &self.attributes {
            if *p != Pred::Label {
                writeln!(f, "  {}: {v}", p.name())?;
            }
        }
        for n in &self.neighbours {
            let arrow = if n.dir == Dir::Out { format!("-{}->", n.pred.name()) } else { format!("<-{}-", n.pred.name()) };
            let mark = if n.pushed { "+" } else { " " };
            let label = n.label.as_deref().map(|l| format!("  \"{}\"", l.chars().take(70).collect::<String>())).unwrap_or_default();
            writeln!(f, "  {mark} {arrow} {}{label}", n.node)?;
        }
        let st = &self.stats;
        let preds: Vec<String> = st.by_pred.iter().map(|(k, v)| format!("{k} {v}")).collect();
        writeln!(f, "  stats: out {} in {} [{}]; held back {}; stack {}; budget left {}; path use {}; {} keys in {}us at T{}",
            st.fan_out, st.fan_in, preds.join(", "), st.held_back, st.stack, st.budget_left, st.path_use, st.keys_read, st.micros, self.session.snapshot)?;
        let top: Vec<&str> = self.session.stack.iter().rev().take(4).map(|fr| fr.node.as_str()).collect();
        if !top.is_empty() {
            writeln!(f, "  next on the stack: {}", top.join(", "))?;
        }
        match &self.token {
            Some(tk) => writeln!(f, "  token: {tk}"),
            None => writeln!(f, "  stack empty: done"),
        }
    }
}
