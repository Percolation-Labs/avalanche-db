//! A query is a session pinned to a snapshot. Each step pops one node off the reasoning
//! stack (the open questions), reads its edges with two prefix scans, pushes what is still
//! to visit within the budget, and returns statistics and a continuation token. The agent
//! reasons between steps. Every step is appended to the usage graph in the same log.

use std::collections::HashSet;
use std::fmt;
use std::time::Instant;

use serde::{Deserialize, Serialize};

use crate::model::{date, lit, FactIn, Pred};
use crate::store::{Dir, Edge, ScanCost, Store};
use crate::Result;

pub const USAGE: &str = "usage";

/// Neighbours described per step; the rest are counted.
const SHOWN: usize = 12;

/// The default walk, most wanted first: why something was decided and what was rejected,
/// then what the decision governs, what carried it out, and what else reports the same. Mechanical links (`mentions`,
/// `parent`, `touches`, `authoredBy`) are left out; ask for them with `--follow`.
pub const DEFAULT_FOLLOW: &[Pred] = &[
    Pred::Because,
    Pred::Rejects,
    Pred::Adopts,
    Pred::Decides,
    Pred::Implements,
    Pred::Fixes,
    Pred::Duplicates,
    Pred::Answers,
    Pred::Makes,
    Pred::Informs,
    Pred::Cites,
];

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Frame {
    pub node: String,
    pub depth: u32,
    /// The node it was reached from, and by which link; None for where the walk began.
    pub parent: Option<String>,
    pub pred: Option<String>,
    pub inbound: bool,
}

impl Frame {
    /// The link as it reads from the parent's side: `duplicates`, or `fixed by`.
    pub fn link(&self) -> String {
        match self.pred.as_deref().and_then(Pred::from_name) {
            Some(p) if self.inbound => p.inverse().to_string(),
            Some(p) => p.name().to_string(),
            None => "start".into(),
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Session {
    pub id: String,
    pub tenant: u32,
    pub start: String,
    pub snapshot: u64,
    /// Walk only what was true on this date (unix seconds); None for now.
    pub valid_at: Option<i64>,
    pub budget: usize,
    pub pushed: usize,
    pub step: u32,
    pub stack: Vec<Frame>,
    pub visited: Vec<Frame>,
    /// Link kinds walked so far, in the order first used.
    pub kinds: Vec<String>,
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
    /// Already visited, or already on the stack.
    pub visited: bool,
    pub known: bool,
    pub id: u64,
}

pub struct StepOut {
    pub session: Session,
    pub at: Option<Frame>,
    pub label: Option<String>,
    pub neighbours: Vec<Neighbour>,
    pub stats: Stats,
    pub token: Option<String>,
}

#[derive(Default)]
pub struct Stats {
    pub fan_out: usize,
    pub fan_in: usize,
    pub opened: usize,
    pub held_back: usize,
    pub open: usize,
    pub budget_left: usize,
    /// Earlier steps, in any session, that visited this node: how worn the path is.
    pub path_use: usize,
    pub keys_read: u64,
    pub micros: u128,
}

/// A node's label and the date it became true, as of a snapshot and a valid date.
pub fn label(store: &Store, t: u32, node: u64, as_of: u64, valid_at: Option<i64>, cost: &mut ScanCost) -> Result<Option<(String, i64)>> {
    for e in store.edges(t, node, Dir::Out, as_of, valid_at, cost)? {
        if e.pred == Pred::Label {
            return Ok(Some((store.name(t, e.other)?.trim_start_matches("lit:").to_string(), e.valid_from)));
        }
    }
    Ok(None)
}

/// Resolve the words to where a walk starts: the best lexical match among labels, run
/// once. A typed name (`issue:SUP-88`) is taken as is.
pub fn resolve(store: &Store, t: u32, words: &str, as_of: u64, valid_at: Option<i64>) -> Result<String> {
    if crate::model::Kind::of(words).is_some() {
        return Ok(words.to_string());
    }
    crate::search::search(store, t, words, as_of, valid_at)?.into_iter().next().map(|h| h.node).ok_or_else(|| format!("nothing known matches {words:?}").into())
}

pub fn ask(store: &Store, t: u32, words: &str, budget: usize, as_of: Option<u64>, valid_at: Option<i64>) -> Result<Session> {
    let head = store.head(t)?;
    let snapshot = as_of.unwrap_or(head).min(head);
    let start = resolve(store, t, words, snapshot, valid_at)?;
    let n = store.by_pred(t, Pred::Asked, head, &mut ScanCost::default())?.len();
    let session = Session {
        id: format!("s{}", n + 1),
        tenant: t,
        start: start.clone(),
        snapshot,
        valid_at,
        budget,
        pushed: 1,
        step: 0,
        stack: vec![Frame { node: start.clone(), depth: 0, parent: None, pred: None, inbound: false }],
        visited: vec![],
        kinds: vec![],
    };
    store.write(t, &[FactIn::new(format!("session:{}", session.id), Pred::Asked, start, USAGE)])?;
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
        return Ok(StepOut { session: s, at: None, label: None, neighbours: vec![], stats, token: None });
    };
    let node = store.id(t, &frame.node)?.ok_or_else(|| format!("{} is not in the store", frame.node))?;
    let usage = store.graph_id(t, USAGE)?;
    let mut edges: Vec<Edge> = store.edges(t, node, Dir::Out, s.snapshot, s.valid_at, &mut cost)?;
    edges.extend(store.edges(t, node, Dir::In, s.snapshot, s.valid_at, &mut cost)?);
    edges.retain(|e| Some(e.graph) != usage);
    if let Some(p) = &frame.pred {
        if !s.kinds.contains(p) {
            s.kinds.push(p.clone());
        }
    }
    s.visited.push(frame.clone());

    let mut label_text = None;
    let mut candidates = vec![];
    for e in &edges {
        if e.dir == Dir::Out {
            stats.fan_out += 1;
        } else {
            stats.fan_in += 1;
        }
        if e.pred == Pred::Label {
            label_text = Some(store.name(t, e.other)?.trim_start_matches("lit:").to_string());
        } else if let Some(rank) = follow.iter().position(|p| *p == e.pred) {
            candidates.push((rank, e.pred, e.dir, e.other));
        }
    }
    // Neighbours stay ids until a reader needs them: a name or a label costs a lookup, so a
    // hub's thousands of held-back edges are counted, not described.
    let visited: HashSet<u64> = s.visited.iter().filter_map(|f| store.id(t, &f.node).ok().flatten()).collect();
    let known: HashSet<u64> = s.stack.iter().filter_map(|f| store.id(t, &f.node).ok().flatten()).chain(visited.iter().copied()).collect();
    // Push lowest priority first so the most wanted link is on top of the stack.
    candidates.sort_by(|a, b| b.0.cmp(&a.0).then(b.3.cmp(&a.3)));
    let mut picked: Vec<(Pred, Dir, u64, bool, bool)> = vec![];
    for (_, pred, dir, other) in candidates {
        let seen = known.contains(&other) || picked.iter().any(|(_, _, o, p, _)| *o == other && *p);
        let pushed = !seen && s.pushed < s.budget;
        if pushed {
            s.pushed += 1;
            stats.opened += 1;
        } else if !seen {
            stats.held_back += 1;
        }
        picked.push((pred, dir, other, pushed, seen));
    }
    let mut neighbours = vec![];
    for (pred, dir, other, pushed, seen) in picked {
        let name = if pushed { store.name(t, other)? } else { String::new() };
        if pushed {
            s.stack.push(Frame { node: name.clone(), depth: frame.depth + 1, parent: Some(frame.node.clone()), pred: Some(pred.name().into()), inbound: dir == Dir::In });
        }
        neighbours.push(Neighbour { pred, dir, label: None, node: name, pushed, visited: visited.contains(&other), known: seen, id: other });
    }
    neighbours.reverse();
    for n in neighbours.iter_mut().take(SHOWN) {
        if n.node.is_empty() {
            n.node = store.name(t, n.id)?;
        }
        n.label = label(store, t, n.id, s.snapshot, s.valid_at, &mut cost)?.map(|(l, _)| l);
    }

    // Path use is read live, not at the snapshot: it is about the store's readers, not its facts.
    let head = store.head(t)?;
    stats.path_use = store.edges(t, node, Dir::In, head, None, &mut cost)?.iter().filter(|e| e.pred == Pred::Visited).count();
    stats.open = s.stack.len();
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
            FactIn::new(&step_node, Pred::Via, lit(frame.pred.as_deref().unwrap_or("start")), USAGE),
            FactIn::new(&step_node, Pred::Returned, lit(&format!("{} edges, {} opened, {} keys", edges.len(), stats.opened, stats.keys_read)), USAGE),
        ],
    )?;
    store.put_session(&s.id, &serde_json::to_string(&s)?)?;
    let token = if s.stack.is_empty() { None } else { Some(s.token()) };
    Ok(StepOut { session: s, at: Some(frame), label: label_text, neighbours, stats, token })
}

impl fmt::Display for StepOut {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let Some(at) = &self.at else {
            return writeln!(f, "no open questions: session {} finished after {} steps", self.session.id, self.session.step);
        };
        let label = self.label.as_deref().map(|l| format!(" \"{l}\"")).unwrap_or_default();
        writeln!(f, "step {}  {}{label}", self.session.step, at.node)?;
        if self.neighbours.len() > SHOWN {
            writeln!(f, "  ({} neighbours; the first {SHOWN} shown)", self.neighbours.len())?;
        }
        for n in self.neighbours.iter().take(SHOWN) {
            let arrow = if n.dir == Dir::Out { format!("-{}->", n.pred.name()) } else { format!("<-{}-", n.pred.name()) };
            let mark = if n.pushed { "+" } else { " " };
            let tail = match (&n.label, n.known) {
                (_, true) if n.visited => "  (visited)".to_string(),
                (_, true) => "  (already open)".to_string(),
                (Some(l), false) => format!("  \"{}\"", l.chars().take(60).collect::<String>()),
                (None, false) => String::new(),
            };
            writeln!(f, "  {mark} {arrow} {}{tail}", n.node)?;
        }
        let st = &self.stats;
        writeln!(f, "  open {} (opened {}, closed 1); link kinds: {}", st.open, st.opened, if self.session.kinds.is_empty() { "none yet".into() } else { self.session.kinds.join(", ") })?;
        writeln!(f, "  stats: out {} in {}; held back {}; budget left {}; path use {}; {} keys in {}µs", st.fan_out, st.fan_in, st.held_back, st.budget_left, st.path_use, st.keys_read, st.micros)?;
        match &self.token {
            Some(tk) => writeln!(f, "  token {tk}"),
            None => writeln!(f, "  no open questions: done"),
        }
    }
}

/// Run a whole walk and return what it reached, in the order visited.
pub fn walk(store: &Store, t: u32, words: &str, budget: usize, valid_at: Option<i64>, follow: &[Pred]) -> Result<Session> {
    let s = ask(store, t, words, budget, None, valid_at)?;
    let mut token = Some(s.token());
    let mut last = s;
    while let Some(tk) = token {
        let out = step(store, &tk, follow)?;
        token = out.token;
        last = out.session;
    }
    Ok(last)
}

/// The walk as a tree for a person: each node under the one it was reached from, with the
/// link as it reads from there and the date the node became true.
pub fn why(store: &Store, s: &Session) -> Result<String> {
    let t = s.tenant;
    let mut out = String::new();
    let mut rows = vec![];
    fn place<'a>(visited: &'a [Frame], node: &str, depth: usize, rows: &mut Vec<(&'a Frame, usize)>) {
        for f in visited.iter().filter(|f| f.parent.as_deref() == Some(node)) {
            rows.push((f, depth));
            place(visited, &f.node, depth + 1, rows);
        }
    }
    if let Some(root) = s.visited.first() {
        rows.push((root, 0));
        place(&s.visited, &root.node, 1, &mut rows);
    }
    let width = rows.iter().map(|(f, d)| d * 2 + if *d == 0 { 0 } else { f.link().len() + 2 } + f.node.len()).max().unwrap_or(0);
    for (f, d) in rows {
        let id = store.id(t, &f.node)?.unwrap();
        let (label, when) = match label(store, t, id, s.snapshot, s.valid_at, &mut ScanCost::default())? {
            Some((l, at)) => (format!(" \"{l}\""), date::show(at)[..10].to_string()),
            None => (String::new(), String::new()),
        };
        let head = if d == 0 { f.node.clone() } else { format!("{}{}  {}", "  ".repeat(d), f.link(), f.node) };
        let pad = width.saturating_sub(head.len());
        out += &format!("{head}{}  {:<10}{label}\n", " ".repeat(pad), when);
    }
    let kinds = s.kinds.len();
    out += &format!("{} steps, {kinds} link kind{}\n", s.step, if kinds == 1 { "" } else { "s" });
    Ok(out)
}
