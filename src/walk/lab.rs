//! WALK: the product's V0 P walk as the walk lab ports it (p8-subsystems `bill/walklab`, `meta/lab/walklab/engine.py`,
//! itself ported read for read from percolate's walk.sql), answered from this store's indexes. Stage A of REM-1172
//! holds it to the lab's engine on the product's recorded runs: the same reads, in the same order, with the same clues.
//!
//! Every rule below is the lab's, and where an order is not the walk's own choice the lab's order is kept:
//!   wave 0     the first `seeds` documents of search's order, of those the graph holds; every read raises clues
//!   wave w>0   the clues the last wave raised are judged; then the wave reads up to w*wave in all: from wave 2 first
//!              `per_wave` search reads, then until full a pending landed document, else the best open accepted clue
//!              (P, or P per unread target under per_target, with P as a float4, ties by key under en_US collation),
//!              else search
//!   clues      term (a term of the read held by at most `cap` documents, its source the first read of the wave
//!              carrying it), next (`beside`), near (`near`); targets are the unread ones, sorted; raised once a walk
//!   stop       after `waves` waves, or a wave that reads nothing
//! The lab's strategy hooks (memory, veto, open_whole) are not here: stage A is the product's walk with them off.

use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet, VecDeque};

use serde::{Deserialize, Serialize};

use crate::construct::lab::{item, tenant_name};
use crate::model::Pred;
use crate::store::{Dir, ScanCost, Store};
use crate::Result;

#[derive(Clone, Debug, Deserialize)]
#[serde(default)]
pub struct Settings {
    pub waves: u32,
    pub wave: usize,
    pub seeds: usize,
    pub per_wave: usize,
    pub cap: usize,
    /// The legacy .5 gate, now a filter (`Gated`): set only to reproduce recorded V0 walks.
    pub gate: Option<f64>,
    /// How opened doors are ordered: `rank` (the decider's order) or the V0 orders `p`, `per_target`, `convergence`.
    pub order: String,
    /// The caller's cap on doors opened per wave; none means until the wave's reads run out.
    pub open: Option<usize>,
    /// The order of reads inside an opened door: `graph` (the door's targets as the graph lists them, sorted; today)
    /// or `postings` (fewest term postings first, the target's own graph degree; the key the tie). Never the question.
    pub within: String,
    /// The most targets one opened door reads; the rest stay unread and the wave's reads go to the next door.
    /// None reads every unread target (today).
    pub per_door: Option<usize>,
}

impl Default for Settings {
    fn default() -> Settings {
        Settings { waves: 10, wave: 50, seeds: 10, per_wave: 10, cap: 100, gate: None, order: "rank".into(), open: None, within: "graph".into(), per_door: None }
    }
}

#[derive(Clone, Debug, Serialize)]
pub struct Clue {
    pub key: String,
    pub kind: String,
    pub x: String,
    pub source: String,
    pub targets: Vec<String>,
    pub wave: u32,
    pub p: Option<f64>,
}

#[derive(Clone, Debug, Serialize)]
pub struct Read {
    pub doc: String,
    pub wave: u32,
    pub ord: usize,
    pub via: Option<String>,
}

#[derive(Debug, Default, Serialize)]
pub struct Walk {
    pub reads: Vec<Read>,
    pub clues: BTreeMap<String, Clue>,
    pub travelled: BTreeMap<String, u32>,
    pub log: Vec<serde_json::Value>,
    pub stop: Option<serde_json::Value>,
    pub keys_read: u64,
    /// Every wave's whole batch: doors shown, their attributes, the filter's result, the full ranking, what opened.
    pub batches: Vec<BatchLog>,
}

/// ORDER BY key under glibc's en_US.utf8: punctuation and spaces ignored at the first level, case after it.
pub fn collate(key: &str) -> (String, String, String) {
    let k = key.to_lowercase();
    (k.chars().filter(|c| c.is_ascii_digit() || c.is_ascii_lowercase()).collect(), k, key.to_string())
}

/// P as Postgres holds it, a float4, read back as a double.
pub fn f4(p: f64) -> f64 {
    p as f32 as f64
}

/// One conversation's graph, read from the store and cached for the walk.
pub struct Graph<'a> {
    store: &'a Store,
    t: u32,
    as_of: u64,
    keys: HashSet<String>,
    cost: ScanCost,
    terms: HashMap<String, Vec<String>>,
    post: HashMap<String, Vec<String>>,
    lists: HashMap<(Pred, String), Vec<String>>,
}

impl<'a> Graph<'a> {
    pub fn open(store: &'a Store, conv: &str) -> Result<Graph<'a>> {
        let t = store.tenant(&tenant_name(conv))?;
        let as_of = store.head(t)?;
        if as_of == 0 {
            return Err(format!("conversation {conv} is not imported").into());
        }
        let mut cost = ScanCost::default();
        let mut keys = HashSet::new();
        for (s, _, _) in store.by_pred(t, Pred::Label, as_of, &mut cost)? {
            keys.insert(strip(&store.name(t, s)?));
        }
        Ok(Graph { store, t, as_of, keys, cost, terms: HashMap::new(), post: HashMap::new(), lists: HashMap::new() })
    }

    fn names(&mut self, node: &str, dir: Dir, pred: Pred) -> Result<Vec<String>> {
        let Some(id) = self.store.id(self.t, node)? else { return Ok(vec![]) };
        let edges = self.store.edges(self.t, id, dir, self.as_of, None, &mut self.cost)?;
        edges.into_iter().filter(|e| e.pred == pred).map(|e| self.store.name(self.t, e.other).map(|n| strip(&n))).collect()
    }

    pub fn holds(&self, doc: &str) -> bool {
        self.keys.contains(doc)
    }

    pub fn terms(&mut self, doc: &str) -> Result<Vec<String>> {
        if !self.terms.contains_key(doc) {
            let v = self.names(&item(doc), Dir::Out, Pred::Tagged)?;
            self.terms.insert(doc.to_string(), v);
        }
        Ok(self.terms[doc].clone())
    }

    /// The documents holding a term: the term's incoming `tagged` edges.
    pub fn post(&mut self, term: &str) -> Result<Vec<String>> {
        if !self.post.contains_key(term) {
            let v = self.names(&format!("lit:{term}"), Dir::In, Pred::Tagged)?;
            self.post.insert(term.to_string(), v);
        }
        Ok(self.post[term].clone())
    }

    pub fn list(&mut self, pred: Pred, doc: &str) -> Result<Vec<String>> {
        let k = (pred, doc.to_string());
        if !self.lists.contains_key(&k) {
            let v = self.names(&item(doc), Dir::Out, pred)?;
            self.lists.insert(k.clone(), v);
        }
        Ok(self.lists[&k].clone())
    }
}

fn strip(name: &str) -> String {
    name.split_once(':').map(|(_, r)| r.to_string()).unwrap_or_else(|| name.to_string())
}

struct State {
    s: Settings,
    order: Vec<String>,
    w: Walk,
    nxt: BTreeMap<String, Clue>,
    reached: HashSet<String>,
    pending: VecDeque<String>,
    si: usize,
    /// Doors the filter kept (all judged doors when there is no filter).
    kept: HashSet<String>,
    /// A door's place in its wave's ranking, for `order: rank` when the decider gave no score.
    rankpos: HashMap<String, (u32, usize)>,
}

/// aiq.walk_state's next-round clues, out of one wave's reads.
fn raise(g: &mut Graph, st: &State, wave_reads: &[String]) -> Result<BTreeMap<String, Clue>> {
    let mut out = BTreeMap::new();
    let mut first_src: Vec<(String, String)> = vec![];
    let mut seen: HashSet<String> = HashSet::new();
    for src in wave_reads {
        for t in g.terms(src)? {
            if !seen.contains(&t) && g.post(&t)?.len() <= st.s.cap && !st.w.clues.contains_key(&format!("term:{t}")) {
                seen.insert(t.clone());
                first_src.push((t, src.clone()));
            }
        }
    }
    for (t, src) in first_src {
        let tg: BTreeSet<String> = g.post(&t)?.into_iter().filter(|d| !st.reached.contains(d)).collect();
        if !tg.is_empty() {
            let k = format!("term:{t}");
            out.insert(k.clone(), Clue { key: k, kind: "term".into(), x: t, source: src, targets: tg.into_iter().collect(), wave: 0, p: None });
        }
    }
    for src in wave_reads {
        for (kind, pred) in [("next", Pred::Beside), ("near", Pred::Near)] {
            let k = format!("{kind}:{src}");
            if st.w.clues.contains_key(&k) || out.contains_key(&k) {
                continue;
            }
            let tg: BTreeSet<String> = g.list(pred, src)?.into_iter().filter(|d| !st.reached.contains(d) && d != src).collect();
            if !tg.is_empty() {
                out.insert(k.clone(), Clue { key: k, kind: kind.into(), x: src.clone(), source: src.clone(), targets: tg.into_iter().collect(), wave: 0, p: None });
            }
        }
    }
    Ok(out)
}

pub use super::doors::{Attrs, Batch, BatchLog, Decider, DoorLabeller, Ranked};

/// Walk with a decider and a labeller; the caller's budget is in `s`.
pub fn run(g: &mut Graph, order: Vec<String>, s: Settings, question: &str, decider: &mut dyn Decider, labeller: &mut dyn DoorLabeller) -> Result<Walk> {
    if !["rank", "p", "per_target", "convergence"].contains(&s.order.as_str()) {
        return Err(format!("order is rank, p, per_target or convergence, not {}", s.order).into());
    }
    if !["graph", "postings"].contains(&s.within.as_str()) {
        return Err(format!("within is graph or postings, not {}", s.within).into());
    }
    if s.per_door == Some(0) {
        return Err("per_door is at least 1".into());
    }
    let mut gated;
    let decider: &mut dyn Decider = match s.gate {
        Some(at) => {
            gated = super::doors::Gated { inner: decider, at };
            &mut gated
        }
        None => decider,
    };
    let mut st = State { s, order, w: Walk::default(), nxt: BTreeMap::new(), reached: HashSet::new(), pending: VecDeque::new(), si: 0, kept: HashSet::new(), rankpos: HashMap::new() };
    let seeds: Vec<String> = st.order.iter().take(st.s.seeds).filter(|d| g.holds(d)).cloned().collect();
    if seeds.is_empty() {
        return Err("no seed: none of search's first documents is in the graph".into());
    }
    st.si = st.s.seeds;
    for (i, d) in seeds.iter().enumerate() {
        st.w.reads.push(Read { doc: d.clone(), wave: 0, ord: i + 1, via: Some("search".into()) });
        st.reached.insert(d.clone());
    }
    st.nxt = raise(g, &st, &seeds)?;
    while step(g, &mut st, question, decider, labeller)? {}
    st.w.keys_read = g.cost.keys_read;
    Ok(st.w)
}

fn step(g: &mut Graph, st: &mut State, question: &str, decider: &mut dyn Decider, labeller: &mut dyn DoorLabeller) -> Result<bool> {
    let wn = 1 + st.w.reads.iter().map(|r| r.wave).max().unwrap_or(0);
    if wn > st.s.waves {
        st.w.stop = Some(serde_json::json!({"reason": "waves", "wave": wn - 1}));
        return Ok(false);
    }
    for c in st.nxt.values_mut() {
        c.wave = wn;
    }
    let nxt = std::mem::take(&mut st.nxt);
    let mut attrs: BTreeMap<String, Attrs> = BTreeMap::new();
    for (k, c) in &nxt {
        attrs.insert(k.clone(), labeller.label(c, g)?);
    }
    let (kept, ranking) = if nxt.is_empty() {
        (None, vec![])
    } else {
        let b = Batch { question, wave: wn, doors: &nxt, attrs: &attrs, reads: &st.w.reads, label_version: labeller.version() };
        let kept = decider.filter(&b)?;
        let ranking = decider.rank(&b)?;
        (kept, ranking)
    };
    let score: HashMap<&str, Option<f64>> = ranking.iter().map(|r| (r.key.as_str(), r.score)).collect();
    let (raised, mut judged, mut accepted) = (nxt.len(), 0, 0);
    for (i, r) in ranking.iter().enumerate() {
        if nxt.contains_key(&r.key) {
            st.rankpos.insert(r.key.clone(), (wn, i));
        }
    }
    let mut doors_log = vec![];
    for (k, mut c) in nxt {
        let ranked = score.contains_key(k.as_str());
        c.p = score.get(k.as_str()).copied().flatten();
        judged += ranked as usize;
        let keep = ranked && kept.as_ref().is_none_or(|ks| ks.contains(&k));
        if keep {
            accepted += 1;
            st.kept.insert(k.clone());
        }
        doors_log.push(serde_json::json!({"key": k, "kind": c.kind, "targets": c.targets, "attrs": attrs.get(&k)}));
        st.w.clues.insert(k, c);
    }
    st.w.log.push(serde_json::json!({"wave": wn, "raised": raised, "judged": judged, "accepted": accepted}));
    st.w.batches.push(BatchLog {
        wave: wn,
        label_version: labeller.version(),
        decider: decider.name(),
        doors: doors_log,
        kept: kept.map(|k| k.into_iter().collect()),
        ranking,
        opened: vec![],
    });
    let mut open: BTreeMap<String, Clue> = st.w.clues.iter()
        .filter(|(k, _)| !st.w.travelled.contains_key(*k) && st.kept.contains(*k))
        .map(|(k, c)| (k.clone(), c.clone())).collect();
    let target = (wn as usize * st.s.wave).saturating_sub(st.w.reads.len());
    let (mut n, mut ord) = (0usize, 0usize);
    let mut wave_reads: Vec<String> = vec![];
    let read = |st: &mut State, doc: String, via: Option<String>, n: &mut usize, ord: &mut usize, wr: &mut Vec<String>| {
        *ord += 1;
        st.w.reads.push(Read { doc: doc.clone(), wave: wn, ord: *ord, via });
        wr.push(doc);
        *n += 1;
    };
    if wn > 1 {
        while n < st.s.per_wave.min(target) && st.si < st.order.len() {
            let doc = st.order[st.si].clone();
            st.si += 1;
            if st.reached.insert(doc.clone()) {
                read(st, doc, Some("search".into()), &mut n, &mut ord, &mut wave_reads);
            }
        }
    }
    let mut best: Option<String> = None;
    let mut opened = 0usize;
    while n < target {
        if let Some(doc) = st.pending.pop_front() {
            read(st, doc, best.clone(), &mut n, &mut ord, &mut wave_reads);
            continue;
        }
        // convergence (REM-1172 stage C, not the product): a clue goes first when its unread targets are where the
        // most open accepted clues converge, one vote per clue; then by P per unread target, as per_target
        let converge = st.s.order == "convergence";
        let mut votes: HashMap<&str, u32> = HashMap::new();
        if converge {
            for c in open.values() {
                for d in c.targets.iter().filter(|d| !st.reached.contains(*d)) {
                    *votes.entry(d.as_str()).or_default() += 1;
                }
            }
        }
        let mut pick: Option<(u32, f64, (String, String, String), String)> = None;
        for (k, c) in &open {
            let u = c.targets.iter().filter(|d| !st.reached.contains(*d)).count();
            if u == 0 {
                continue;
            }
            let p = f4(c.p.unwrap_or(0.0));
            let score = match st.s.order.as_str() {
                // the decider's order: its score where it gave one, else its place (earlier waves' doors first)
                "rank" => c.p.unwrap_or_else(|| {
                    let (w, i) = st.rankpos.get(k).copied().unwrap_or((u32::MAX, usize::MAX));
                    -(w as f64) * 1e6 - i as f64
                }),
                "p" => p,
                _ => p / u as f64,
            };
            let v = if converge { c.targets.iter().filter(|d| !st.reached.contains(*d)).map(|d| votes[d.as_str()]).max().unwrap_or(0) } else { 0 };
            let col = collate(k);
            let better = match &pick {
                None => true,
                Some((bv, bs, bc, _)) => v > *bv || (v == *bv && (score > *bs || (score == *bs && col < *bc))),
            };
            if better {
                pick = Some((v, score, col, k.clone()));
            }
        }
        let pick = pick.map(|(_, s, c, k)| (s, c, k));
        let capped = st.s.open.is_some_and(|cap| opened >= cap);
        if let (Some((_, _, k)), false) = (pick, capped) {
            opened += 1;
            if let Some(b) = st.w.batches.last_mut() {
                b.opened.push(k.clone());
            }
            let c = open.remove(&k).unwrap();
            let mut unread: Vec<String> = c.targets.iter().filter(|d| !st.reached.contains(*d)).cloned().collect();
            if st.s.within == "postings" {
                let mut keyed = Vec::with_capacity(unread.len());
                for d in unread {
                    keyed.push((g.terms(&d)?.len(), d));
                }
                keyed.sort();
                unread = keyed.into_iter().map(|(_, d)| d).collect();
            }
            if let Some(m) = st.s.per_door {
                unread.truncate(m);
            }
            for d in unread {
                st.reached.insert(d.clone());
                st.pending.push_back(d);
            }
            st.w.travelled.insert(k.clone(), wn);
            best = Some(k);
            continue;
        }
        if st.si >= st.order.len() {
            break;
        }
        let doc = st.order[st.si].clone();
        st.si += 1;
        if st.reached.insert(doc.clone()) {
            read(st, doc, Some("search".into()), &mut n, &mut ord, &mut wave_reads);
        }
    }
    if n == 0 {
        st.w.stop = Some(serde_json::json!({"reason": "dry", "wave": wn}));
        return Ok(false);
    }
    st.nxt = raise(g, st, &wave_reads)?;
    Ok(true)
}
