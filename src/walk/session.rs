//! A query is a session pinned to a snapshot. The open questions are a frontier, ranked by
//! a priority policy the session holds: a weight per link kind, the value landscape that
//! tilts the walk away from wandering. Each step takes the best open question (or the one
//! the agent names), reads its links with two prefix scans, opens what it reaches within
//! the budget, and returns the ranked frontier and a continuation token. The agent may
//! change the policy at any step. Every step is logged in the tenant's usage log, which has
//! its own transactions, so walking never moves the data's T.

use std::collections::{BTreeMap, HashSet};
use std::fmt;
use std::time::Instant;

use serde::{Deserialize, Serialize};

use crate::model::{date, lit, FactIn, Pred};
use crate::store::{Dir, Edge, ScanCost, Store};
use crate::Result;

/// Neighbours described per step; the rest are counted.
const SHOWN: usize = 12;
/// Each hop away from the start is worth this much less.
const DEPTH_DECAY: f64 = 0.9;

/// The default policy: why something was decided and what was rejected first, then what
/// carried it out and what it governs, then what else reports the same. Kinds left out
/// (mentions, parent, touches, authoredBy) weigh 0 and are not followed.
pub const DEFAULT_POLICY: &[(Pred, f64)] = &[
    (Pred::Because, 1.0),
    (Pred::Rejects, 0.9),
    (Pred::Adopts, 0.9),
    (Pred::Answers, 0.8),
    (Pred::Implements, 0.8),
    (Pred::Fixes, 0.8),
    (Pred::Challenges, 0.8),
    (Pred::Supports, 0.7),
    (Pred::Informs, 0.7),
    (Pred::Decides, 0.6),
    (Pred::MergedAs, 0.6),
    (Pred::Duplicates, 0.5),
    (Pred::Makes, 0.5),
    (Pred::Cites, 0.3),
];

pub type Policy = BTreeMap<String, f64>;

pub fn default_policy() -> Policy {
    DEFAULT_POLICY.iter().map(|(p, w)| (p.name().to_string(), *w)).collect()
}

/// `because=1,mentions=0.4`
pub fn parse_prefer(s: &[String]) -> Result<Vec<(String, f64)>> {
    s.iter()
        .map(|kv| {
            let (k, v) = kv.split_once('=').ok_or_else(|| format!("{kv}: want kind=weight"))?;
            Pred::from_name(k).ok_or_else(|| format!("{k}: not a link type"))?;
            Ok((k.to_string(), v.parse::<f64>().map_err(|_| format!("{v}: not a weight"))?))
        })
        .collect()
}

fn fmt_prefs(p: &[(String, f64)]) -> String {
    p.iter().map(|(k, w)| format!("{k}={w}")).collect::<Vec<_>>().join(",")
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Frame {
    pub node: String,
    pub depth: u32,
    /// The node it was reached from, and by which link; None for where the walk began.
    pub parent: Option<String>,
    pub pred: Option<String>,
    pub inbound: bool,
    pub priority: f64,
    /// When it was opened, to break ties in favour of the older question.
    pub order: usize,
    /// Reached over a link the dream decided, not one a source states.
    #[serde(default)]
    pub dreamed: bool,
}

impl Frame {
    /// The link as it reads from the parent's side: `rejects`, or `fixed by`.
    pub fn link(&self) -> String {
        match self.pred.as_deref().and_then(Pred::from_name) {
            Some(p) if self.inbound => p.inverse().to_string(),
            Some(p) => p.name().to_string(),
            None => "start".into(),
        }
    }

    /// `parent link node`, or the node alone where the walk began.
    pub fn line(&self) -> String {
        match &self.parent {
            Some(p) => format!("{p} {} {}", self.link(), self.node),
            None => self.node.clone(),
        }
    }

    fn rescore(&mut self, policy: &Policy) {
        let w = self.pred.as_ref().map(|p| policy.get(p).copied().unwrap_or(0.0)).unwrap_or(1.0);
        self.priority = w * DEPTH_DECAY.powi(self.depth as i32);
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Session {
    pub id: String,
    pub tenant: u32,
    /// The tenant's usage log.
    pub usage: u32,
    pub start: String,
    pub snapshot: u64,
    /// Walk only what was true at this time (unix seconds); None for now.
    pub valid_at: Option<i64>,
    pub budget: usize,
    pub opened: usize,
    pub step: u32,
    pub policy: Policy,
    pub frontier: Vec<Frame>,
    pub visited: Vec<Frame>,
    /// Link kinds walked so far, in the order first used.
    pub kinds: Vec<String>,
    /// What the steps so far cost: index keys read, and time.
    #[serde(default)]
    pub keys_read: u64,
    #[serde(default)]
    pub micros: u128,
}

impl Session {
    /// What `midb ask` prints: where the walk starts, what it is pinned to, and its token.
    pub fn started(&self) -> String {
        format!("session {} at {}, pinned to T{}, budget {}\n  token {}\n", self.id, self.start, self.snapshot, self.budget, self.token())
    }

    /// Which state a walk saw: `T2`, or `2026-04-10` when pinned to a valid time.
    pub fn as_of_label(&self) -> String {
        match self.valid_at {
            Some(v) => date::show(v)[..10].to_string(),
            None => format!("T{}", self.snapshot),
        }
    }

    pub fn token(&self) -> String {
        format!("{}.{}.{}", self.id, self.step, self.snapshot)
    }

    fn key(&self) -> String {
        format!("{}/{}", self.usage, self.id)
    }

    /// The open questions, best first.
    pub fn ranked(&self) -> Vec<&Frame> {
        let mut v: Vec<&Frame> = self.frontier.iter().collect();
        v.sort_by(|a, b| b.priority.total_cmp(&a.priority).then(a.order.cmp(&b.order)));
        v
    }

    fn prefer(&mut self, prefs: &[(String, f64)]) {
        for (k, w) in prefs {
            self.policy.insert(k.clone(), *w);
        }
        let policy = self.policy.clone();
        self.frontier.iter_mut().for_each(|f| f.rescore(&policy));
    }
}

/// How the agent steers one step: change the policy, and/or take a named open question.
#[derive(Default)]
pub struct Steer {
    pub prefer: Vec<(String, f64)>,
    pub take: Option<String>,
}

pub struct Neighbour {
    pub pred: Pred,
    pub dir: Dir,
    pub node: String,
    pub label: Option<String>,
    /// The priority it was opened at, if this step opened it.
    pub opened: Option<f64>,
    pub visited: bool,
    pub known: bool,
    pub id: u64,
    /// The link was decided by the dream, not stated by a source.
    pub dreamed: bool,
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
    pub budget_left: usize,
    /// Earlier steps, in any session, that visited this node: how worn the path is.
    pub path_use: usize,
    pub keys_read: u64,
    pub micros: u128,
}

/// A node's label and the date it became true, as of a snapshot and a valid time.
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
    super::search::search(store, t, words, as_of, valid_at)?.into_iter().next().map(|h| h.node).ok_or_else(|| format!("nothing known matches {words:?}").into())
}

pub fn ask(store: &Store, t: u32, words: &str, budget: usize, as_of: Option<u64>, valid_at: Option<i64>, prefer: &[(String, f64)]) -> Result<Session> {
    let head = store.head(t)?;
    let snapshot = as_of.unwrap_or(head).min(head);
    let start = resolve(store, t, words, snapshot, valid_at)?;
    let usage = store.usage_of(t)?;
    let n = store.by_pred(usage, Pred::Asked, store.head(usage)?, &mut ScanCost::default())?.len();
    let mut s = Session {
        id: format!("s{}", n + 1),
        tenant: t,
        usage,
        start: start.clone(),
        snapshot,
        valid_at,
        budget,
        opened: 1,
        step: 0,
        policy: default_policy(),
        frontier: vec![Frame { node: start.clone(), depth: 0, parent: None, pred: None, inbound: false, priority: 1.0, order: 0, dreamed: false }],
        visited: vec![],
        kinds: vec![],
        keys_read: 0,
        micros: 0,
    };
    s.prefer(prefer);
    let session = format!("session:{}", s.id);
    let mut facts = vec![FactIn::new(&session, Pred::Asked, start, "usage")];
    if !prefer.is_empty() {
        facts.push(FactIn::new(&session, Pred::Prefer, lit(&fmt_prefs(prefer)), "usage"));
    }
    store.write(usage, &facts)?;
    store.put_session(&s.key(), &serde_json::to_string(&s)?)?;
    Ok(s)
}

pub fn load(store: &Store, t: u32, token: &str) -> Result<Session> {
    let mut parts = token.split('.');
    let (id, step, snap) = (parts.next().unwrap_or(""), parts.next().and_then(|s| s.parse::<u32>().ok()), parts.next().and_then(|s| s.parse::<u64>().ok()));
    let usage = store.usage_of(t)?;
    let json = store.get_session(&format!("{usage}/{id}"))?.ok_or_else(|| format!("no session {id}"))?;
    let s: Session = serde_json::from_str(&json)?;
    if step != Some(s.step) || snap != Some(s.snapshot) {
        return Err(format!("stale token {token}: session {id} is at {}", s.token()).into());
    }
    Ok(s)
}

pub fn step(store: &Store, t: u32, token: &str, steer: &Steer) -> Result<StepOut> {
    let started = Instant::now();
    let mut s = load(store, t, token)?;
    let mut cost = ScanCost::default();
    let mut stats = Stats::default();
    s.prefer(&steer.prefer);
    let best = s.ranked().first().map(|f| f.node.clone());
    let Some(name) = steer.take.clone().or(best) else {
        return Ok(StepOut { session: s, at: None, label: None, neighbours: vec![], stats, token: None });
    };
    let pick = s.frontier.iter().position(|f| f.node == name).ok_or_else(|| format!("{name} is not an open question here"))?;
    let frame = s.frontier.remove(pick);
    let node = store.id(t, &frame.node)?.ok_or_else(|| format!("{} is not in the store", frame.node))?;
    let mut edges: Vec<Edge> = store.edges(t, node, Dir::Out, s.snapshot, s.valid_at, &mut cost)?;
    edges.extend(store.edges(t, node, Dir::In, s.snapshot, s.valid_at, &mut cost)?);
    if let Some(p) = &frame.pred {
        if !s.kinds.contains(p) {
            s.kinds.push(p.clone());
        }
    }
    s.visited.push(frame.clone());

    let mut label_text = None;
    let mut candidates = vec![];
    let dream = store.graph_id(t, "dream")?;
    for e in &edges {
        if e.dir == Dir::Out {
            stats.fan_out += 1;
        } else {
            stats.fan_in += 1;
        }
        if e.pred == Pred::Label {
            label_text = Some(store.name(t, e.other)?.trim_start_matches("lit:").to_string());
        } else if s.policy.get(e.pred.name()).is_some_and(|w| *w > 0.0) {
            candidates.push((e.pred, e.dir, e.other, Some(e.graph) == dream));
        }
    }
    // Neighbours stay ids until a reader needs them: a name or a label costs a lookup, so a
    // hub's thousands of held-back edges are counted, not described.
    let visited: HashSet<u64> = s.visited.iter().filter_map(|f| store.id(t, &f.node).ok().flatten()).collect();
    let known: HashSet<u64> = s.frontier.iter().filter_map(|f| store.id(t, &f.node).ok().flatten()).chain(visited.iter().copied()).collect();
    let mut opened_now: HashSet<u64> = HashSet::new();
    let mut neighbours = vec![];
    for (pred, dir, other, dreamed) in candidates {
        let seen = known.contains(&other) || opened_now.contains(&other);
        let mut opened = None;
        if !seen && s.opened < s.budget {
            let mut f = Frame { node: store.name(t, other)?, depth: frame.depth + 1, parent: Some(frame.node.clone()), pred: Some(pred.name().into()), inbound: dir == Dir::In, priority: 0.0, order: s.opened, dreamed };
            f.rescore(&s.policy);
            opened = Some(f.priority);
            s.opened += 1;
            stats.opened += 1;
            opened_now.insert(other);
            s.frontier.push(f);
        } else if !seen {
            stats.held_back += 1;
        }
        neighbours.push(Neighbour { pred, dir, label: None, node: String::new(), opened, visited: visited.contains(&other), known: seen, id: other, dreamed });
    }
    neighbours.sort_by(|a, b| b.opened.unwrap_or(-1.0).total_cmp(&a.opened.unwrap_or(-1.0)));
    for n in neighbours.iter_mut().take(SHOWN) {
        n.node = store.name(t, n.id)?;
        n.label = label(store, t, n.id, s.snapshot, s.valid_at, &mut cost)?.map(|(l, _)| l);
    }

    let uhead = store.head(s.usage)?;
    stats.path_use = match store.id(s.usage, &frame.node)? {
        Some(uid) => store.edges(s.usage, uid, Dir::In, uhead, None, &mut cost)?.iter().filter(|e| e.pred == Pred::Visited).count(),
        None => 0,
    };
    stats.budget_left = s.budget.saturating_sub(s.opened);
    stats.keys_read = cost.keys_read;
    stats.micros = started.elapsed().as_micros();
    s.keys_read += stats.keys_read;
    s.micros += stats.micros;

    s.step += 1;
    let step_node = format!("step:{}-{}", s.id, s.step);
    let mut facts = vec![
        FactIn::new(&step_node, Pred::InSession, format!("session:{}", s.id), "usage"),
        FactIn::new(&step_node, Pred::Visited, &frame.node, "usage"),
        FactIn::new(&step_node, Pred::Via, lit(frame.pred.as_deref().unwrap_or("start")), "usage"),
        FactIn::new(&step_node, Pred::Returned, lit(&format!("{} edges, {} opened, {} keys", edges.len(), stats.opened, stats.keys_read)), "usage"),
    ];
    if !steer.prefer.is_empty() {
        facts.push(FactIn::new(&step_node, Pred::Prefer, lit(&fmt_prefs(&steer.prefer)), "usage"));
    }
    if let Some(name) = &steer.take {
        facts.push(FactIn::new(&step_node, Pred::Took, lit(name), "usage"));
    }
    store.write(s.usage, &facts)?;
    store.put_session(&s.key(), &serde_json::to_string(&s)?)?;
    let token = if s.frontier.is_empty() { None } else { Some(s.token()) };
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
            let arrow = if n.dreamed { format!("{arrow} (dreamed, not stated)") } else { arrow };
            let (mark, tail) = match (n.opened, n.known, &n.label) {
                (Some(p), _, Some(l)) => ("+", format!("  \"{}\"  {p:.2}", crate::model::short(l, 60))),
                (Some(p), _, None) => ("+", format!("  {p:.2}")),
                (None, true, _) if n.visited => (" ", "  (visited)".to_string()),
                (None, true, _) => (" ", "  (already open)".to_string()),
                (None, false, _) => (" ", "  (over budget)".to_string()),
            };
            writeln!(f, "  {mark} {arrow} {}{tail}", n.node)?;
        }
        let st = &self.stats;
        let ranked = self.session.ranked();
        let next: Vec<String> = ranked.iter().take(3).map(|fr| format!("{} {:.2}", fr.node, fr.priority)).collect();
        writeln!(f, "  open {} (opened {}, closed 1); next: {}", ranked.len(), st.opened, if next.is_empty() { "none".into() } else { next.join(", ") })?;
        writeln!(f, "  stats: out {} in {}; held back {}; budget left {}; path use {}; {} keys in {}µs", st.fan_out, st.fan_in, st.held_back, st.budget_left, st.path_use, st.keys_read, st.micros)?;
        match &self.token {
            Some(tk) => writeln!(f, "  token {tk}"),
            None => writeln!(f, "  no open questions: done"),
        }
    }
}

/// Run a whole walk, always taking the best open question, and return the session.
pub fn walk(store: &Store, t: u32, words: &str, budget: usize, as_of: Option<u64>, valid_at: Option<i64>, prefer: &[(String, f64)]) -> Result<Session> {
    let s = ask(store, t, words, budget, as_of, valid_at, prefer)?;
    let mut token = Some(s.token());
    let mut last = s;
    while let Some(tk) = token {
        let out = step(store, t, &tk, &Steer::default())?;
        token = out.token;
        last = out.session;
    }
    Ok(last)
}

/// What a walk reached, one line per record: `parent link node`, with the start alone.
/// Two walks reached the same answer when these sets match.
pub fn reached(s: &Session) -> Vec<String> {
    s.visited.iter().map(Frame::line).collect()
}

/// The walk as a tree for a person: each node under the one it was reached from, with the
/// link as it reads from there and the date the node became true. Given an earlier walk of
/// the same question, records it did not reach are marked `+`, and records it reached
/// that this walk does not are listed after the tree, marked `-`.
pub fn why(store: &Store, s: &Session, then: Option<&Session>) -> Result<String> {
    let t = s.tenant;
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
    // A link the dream decided says so, because a reader cannot tell it from a stated one
    // (REM-1331 round 6: six of six agents repeated a wrong dreamed link as fact).
    let heads: Vec<String> = rows.iter().map(|(f, d)| if *d == 0 { f.node.clone() } else { format!("{}{}{}  {}", "  ".repeat(*d), f.link(), if f.dreamed { " (dreamed, not stated)" } else { "" }, f.node) }).collect();
    let width = heads.iter().map(|h| h.chars().count()).max().unwrap_or(0);
    let before: Option<HashSet<String>> = then.map(|p| reached(p).into_iter().collect());
    let mut out = String::new();
    for ((f, _), head) in rows.iter().zip(&heads) {
        let id = store.id(t, &f.node)?.unwrap();
        let (label, when) = match label(store, t, id, s.snapshot, s.valid_at, &mut ScanCost::default())? {
            Some((l, at)) => (format!(" \"{}\"", crate::model::short(&l, 60)), date::show(at)[..10].to_string()),
            None => (String::new(), String::new()),
        };
        let mark = match &before {
            None => "",
            Some(b) if b.contains(&f.line()) => "  ",
            Some(_) => "+ ",
        };
        out += &format!("{mark}{head}{}  {when:<10}{label}\n", " ".repeat(width - head.chars().count()));
    }
    let kinds = s.kinds.len();
    out += &format!("{} steps, {kinds} link kind{}; {} keys read in {:.1?}\n", s.step, if kinds == 1 { "" } else { "s" }, s.keys_read, std::time::Duration::from_micros(s.micros as u64));
    if let Some(then) = then {
        let now: HashSet<String> = reached(s).into_iter().collect();
        let gone: Vec<String> = reached(then).into_iter().filter(|r| !now.contains(r)).collect();
        for g in &gone {
            out += &format!("- {g}\n");
        }
        let added = now.len() - now.iter().filter(|r| before.as_ref().unwrap().contains(*r)).count();
        out += &format!("against {}: {added} reached since, {} no longer reached\n", then.as_of_label(), gone.len());
    }
    Ok(out)
}
