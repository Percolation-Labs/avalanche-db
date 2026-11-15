//! DOORS: what a connection wave chooses between, and the two parts that choose (specs/doors.md).
//!
//! A door labeller describes doors from the graph alone; its signature has no question, so a door can never carry
//! the question or its gold. A decider filters the doors on their attributes (optional) and ranks what is left;
//! the walk opens the top of the ranking until the caller's budget runs out. Every wave's whole batch is logged, so
//! any decider can be scored as a ranker on recorded batches without walking (`rescore`, `rank_metrics`).
//!
//! The deciders here are fakes for testing the seams (oracle, random, search order, fixed scores, an attribute
//! filter) and the legacy gate as a filter. Real deciders plug in through the same trait.

use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};

use serde::{Deserialize, Serialize};

use super::explore::Coin;
use super::lab::{collate, Clue, Graph, Read, Walk};
use crate::Result;

/// What a labeller says about one door. Graph-derived only.
#[derive(Clone, Debug, Default, Serialize, Deserialize, PartialEq)]
pub struct Attrs {
    /// The door's type: the clue kind (`term`, `next`, `near`) or the predicate it follows.
    pub kind: String,
    /// What is right behind the door.
    pub immediate: Vec<String>,
    /// A compressed summary of what is reachable through it, when a labeller builds one.
    pub reachable: Option<String>,
    /// Graph statistics a filter can use: `targets`, `postings`, ...
    pub stats: BTreeMap<String, f64>,
}

/// Describes doors from the graph. There is no question argument, by design (Sirsh, M-20261115-201816-ab76).
pub trait DoorLabeller {
    fn version(&self) -> String;
    fn label(&mut self, door: &Clue, g: &mut Graph) -> Result<Attrs>;
}

/// The default labeller: the door's kind, its first three targets, its unread target count and, for a term, the
/// term's postings. No reachable summary.
pub struct GraphStats;

impl DoorLabeller for GraphStats {
    fn version(&self) -> String {
        "graph-stats/1".into()
    }
    fn label(&mut self, door: &Clue, g: &mut Graph) -> Result<Attrs> {
        let mut stats = BTreeMap::new();
        stats.insert("targets".into(), door.targets.len() as f64);
        if door.kind == "term" {
            stats.insert("postings".into(), g.post(&door.x)?.len() as f64);
        }
        Ok(Attrs { kind: door.kind.clone(), immediate: door.targets.iter().take(3).cloned().collect(), reachable: None, stats })
    }
}

/// A labeller that says only the door's kind: the cheapest possible door, for tests.
pub struct KindOnly;

impl DoorLabeller for KindOnly {
    fn version(&self) -> String {
        "kind-only/1".into()
    }
    fn label(&mut self, door: &Clue, _g: &mut Graph) -> Result<Attrs> {
        Ok(Attrs { kind: door.kind.clone(), ..Attrs::default() })
    }
}

/// One wave's doors, as a decider sees them.
pub struct Batch<'a> {
    pub question: &'a str,
    pub wave: u32,
    pub doors: &'a BTreeMap<String, Clue>,
    pub attrs: &'a BTreeMap<String, Attrs>,
    pub reads: &'a [Read],
    pub label_version: String,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct Ranked {
    pub key: String,
    pub score: Option<f64>,
}

/// One wave of the walk's log: every door shown, with its attributes, and what the decider and the budget did.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct BatchLog {
    pub wave: u32,
    pub label_version: String,
    pub decider: String,
    /// {key, kind, targets, attrs} per door, in key order.
    pub doors: Vec<serde_json::Value>,
    /// The filter's kept set, or none when the decider did not filter.
    pub kept: Option<Vec<String>>,
    /// The full ranking, best first.
    pub ranking: Vec<Ranked>,
    /// The doors opened while this wave read, in order (they may have been raised by earlier waves).
    pub opened: Vec<String>,
}

pub trait Decider {
    fn name(&self) -> String;
    /// The reduction pass: the doors to keep, judged on their attributes; none means keep every ranked door.
    fn filter(&mut self, _b: &Batch) -> Result<Option<BTreeSet<String>>> {
        Ok(None)
    }
    /// The ranking pass: best first. A door left out is unjudged and never opened.
    fn rank(&mut self, b: &Batch) -> Result<Vec<Ranked>>;
}

/// Sort by score, highest first, ties by key under the walk's collation.
fn by_score(mut v: Vec<(String, f64)>) -> Vec<Ranked> {
    v.sort_by(|a, b| b.1.total_cmp(&a.1).then_with(|| collate(&a.0).cmp(&collate(&b.0))));
    v.into_iter().map(|(key, s)| Ranked { key, score: Some(s) }).collect()
}

/// Fixed scores by key, from a recording or a function. A key with no score is left unjudged.
pub struct Scores<F: FnMut(&str) -> Option<f64>>(pub String, pub F);

impl<F: FnMut(&str) -> Option<f64>> Decider for Scores<F> {
    fn name(&self) -> String {
        self.0.clone()
    }
    fn rank(&mut self, b: &Batch) -> Result<Vec<Ranked>> {
        Ok(by_score(b.doors.keys().filter_map(|k| (self.1)(k).map(|p| (k.clone(), p))).collect()))
    }
}

/// The V0 gate, as a filter: keeps the doors `inner` scores at `at` or above, and ranks as `inner` does.
pub struct Gated<'d> {
    pub inner: &'d mut dyn Decider,
    pub at: f64,
}

impl Decider for Gated<'_> {
    fn name(&self) -> String {
        format!("{} gated at {}", self.inner.name(), self.at)
    }
    fn filter(&mut self, b: &Batch) -> Result<Option<BTreeSet<String>>> {
        let inner_kept = self.inner.filter(b)?;
        let r = self.inner.rank(b)?;
        Ok(Some(r.into_iter()
            .filter(|x| x.score.is_some_and(|p| p >= self.at) && inner_kept.as_ref().is_none_or(|k| k.contains(&x.key)))
            .map(|x| x.key).collect()))
    }
    fn rank(&mut self, b: &Batch) -> Result<Vec<Ranked>> {
        self.inner.rank(b)
    }
}

/// Knows the gold: a door ranks by how many gold documents it leads to, then by fewer targets. The upper bound on
/// any decider for these doors, and a test of what a door must show for a decider to find gold.
pub struct Oracle(pub HashSet<String>);

impl Decider for Oracle {
    fn name(&self) -> String {
        "oracle".into()
    }
    fn rank(&mut self, b: &Batch) -> Result<Vec<Ranked>> {
        Ok(by_score(b.doors.iter().map(|(k, c)| {
            let gold = c.targets.iter().filter(|d| self.0.contains(*d)).count() as f64;
            (k.clone(), gold + 1.0 / (1.0 + c.targets.len() as f64))
        }).collect()))
    }
}

/// A seeded shuffle: chance, for a ranking metric's floor.
pub struct Random(pub Coin);

impl Decider for Random {
    fn name(&self) -> String {
        "random".into()
    }
    fn rank(&mut self, b: &Batch) -> Result<Vec<Ranked>> {
        Ok(by_score(b.doors.keys().map(|k| (k.clone(), self.0.next())).collect()))
    }
}

/// Search's order at an equal budget: a door ranks by the best search position among its targets. The baseline.
pub struct SearchOrder(pub HashMap<String, usize>);

impl SearchOrder {
    pub fn new(order: &[String]) -> SearchOrder {
        SearchOrder(order.iter().enumerate().map(|(i, d)| (d.clone(), i)).collect())
    }
}

impl Decider for SearchOrder {
    fn name(&self) -> String {
        "search-order".into()
    }
    fn rank(&mut self, b: &Batch) -> Result<Vec<Ranked>> {
        Ok(by_score(b.doors.iter().map(|(k, c)| {
            let best = c.targets.iter().filter_map(|d| self.0.get(d)).min().copied().unwrap_or(usize::MAX);
            (k.clone(), -(best as f64))
        }).collect()))
    }
}

/// Filter-then-rank: keep the doors whose statistic `stat` is at most `max` (a door without it is dropped), then
/// rank with `inner`. A fake for testing the two passes, not a proposal for which attribute matters.
pub struct AttrFilter<D: Decider> {
    pub stat: String,
    pub max: f64,
    pub inner: D,
}

impl<D: Decider> Decider for AttrFilter<D> {
    fn name(&self) -> String {
        format!("{} <= {} then {}", self.stat, self.max, self.inner.name())
    }
    fn filter(&mut self, b: &Batch) -> Result<Option<BTreeSet<String>>> {
        Ok(Some(b.attrs.iter().filter(|(_, a)| a.stats.get(&self.stat).is_some_and(|v| *v <= self.max)).map(|(k, _)| k.clone()).collect()))
    }
    fn rank(&mut self, b: &Batch) -> Result<Vec<Ranked>> {
        self.inner.rank(b)
    }
}

/// Re-rank every recorded batch of a walk with another decider, without walking. Doors and attributes come from the
/// log; the reads are the walk's reads before that wave. Returns (wave, the decider's filter, its ranking).
pub fn rescore(w: &Walk, question: &str, d: &mut dyn Decider) -> Result<Vec<(u32, Option<BTreeSet<String>>, Vec<Ranked>)>> {
    let mut out = vec![];
    for b in &w.batches {
        let mut doors = BTreeMap::new();
        let mut attrs = BTreeMap::new();
        for v in &b.doors {
            let key = v["key"].as_str().ok_or("a logged door has no key")?.to_string();
            let targets: Vec<String> = serde_json::from_value(v["targets"].clone())?;
            let kind = v["kind"].as_str().unwrap_or_default().to_string();
            doors.insert(key.clone(), Clue { key: key.clone(), kind, x: String::new(), source: String::new(), targets, wave: b.wave, p: None });
            attrs.insert(key, serde_json::from_value(v["attrs"].clone()).unwrap_or_default());
        }
        let reads: Vec<Read> = w.reads.iter().filter(|r| r.wave < b.wave).cloned().collect();
        let batch = Batch { question, wave: b.wave, doors: &doors, attrs: &attrs, reads: &reads, label_version: b.label_version.clone() };
        let kept = d.filter(&batch)?;
        let r = d.rank(&batch)?;
        out.push((b.wave, kept, r));
    }
    Ok(out)
}

/// A ranking's quality against oracle labels: MRR (first relevant), NDCG@k (binary gain) and recall@k.
#[derive(Clone, Debug, Serialize, PartialEq)]
pub struct RankMetrics {
    pub mrr: f64,
    pub ndcg: f64,
    pub recall: f64,
    pub relevant: usize,
}

pub fn rank_metrics(ranking: &[String], relevant: &HashSet<String>, k: usize) -> RankMetrics {
    let first = ranking.iter().position(|x| relevant.contains(x));
    let mrr = first.map(|i| 1.0 / (i as f64 + 1.0)).unwrap_or(0.0);
    let dcg: f64 = ranking.iter().take(k).enumerate().filter(|(_, x)| relevant.contains(*x)).map(|(i, _)| 1.0 / (i as f64 + 2.0).log2()).sum();
    let ideal: f64 = (0..relevant.len().min(k)).map(|i| 1.0 / (i as f64 + 2.0).log2()).sum();
    let hit = ranking.iter().take(k).filter(|x| relevant.contains(*x)).count();
    RankMetrics {
        mrr,
        ndcg: if ideal > 0.0 { dcg / ideal } else { 0.0 },
        recall: if relevant.is_empty() { 0.0 } else { hit as f64 / relevant.len() as f64 },
        relevant: relevant.len(),
    }
}

/// The doors of a logged batch that lead to gold: the oracle labels a ranking is scored against.
pub fn relevant(b: &BatchLog, gold: &HashSet<String>) -> HashSet<String> {
    b.doors.iter().filter(|v| v["targets"].as_array().is_some_and(|t| t.iter().any(|d| d.as_str().is_some_and(|d| gold.contains(d)))))
        .filter_map(|v| v["key"].as_str().map(String::from)).collect()
}
