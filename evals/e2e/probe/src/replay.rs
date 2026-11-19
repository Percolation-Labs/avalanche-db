//! E2E_REPLAY: the k=10 walk re-run with Jev's recorded scores (from `midb walk --trace` replays), under other pick
//! orders, at $0. A door no recorded batch scored is left unranked, so it is never opened; each walk counts the
//! doors that happened to (`unknown`), the measure of how far a counterfactual walk left the recorded one.
//! E2E_ORDERS picks the orders (default rank,per_target); per_read needs evals/width/per_read.patch on lab.rs.

use std::collections::{HashMap, HashSet};
use std::io::Write;

use avalanche::walk::d6::D6;
use avalanche::walk::doors::{Batch, Decider, Ranked};
use avalanche::walk::lab::{run as walk, Graph, Settings};
use avalanche::walk::text::FullText;

use crate::features::Links;
use crate::votes::{wppr, Edges};

/// evals/walkvote/REGISTERED.md: P fused with X by reciprocal rank (60), over the doors with a recorded P.
/// mode: none (P alone), vote (mean read-set PPR per unread target at θ), shuffled (the same on shuffled links), narrow.
struct Fused<'a, 'g, 'd> {
    r: Replay,
    mode: String,
    th: (f64, f64),
    g: &'g mut Graph<'a>,
    real: &'g mut Edges<'d>,
    shuf: &'g mut Edges<'d>,
}

impl Decider for Fused<'_, '_, '_> {
    fn name(&self) -> String {
        format!("fused:{}", self.mode)
    }
    fn rank(&mut self, b: &Batch) -> avalanche::Result<Vec<Ranked>> {
        let known = self.r.rank(b)?;
        if self.mode == "none" || known.len() < 2 {
            return Ok(known);
        }
        let read: Vec<String> = b.reads.iter().map(|r| r.doc.clone()).collect();
        let rs: HashSet<&String> = read.iter().collect();
        let pr = match self.mode.as_str() {
            "vote" | "learned" if !read.is_empty() => Some(wppr(self.g, self.real, &read, self.th)?),
            "shuffled" if !read.is_empty() => Some(wppr(self.g, self.shuf, &read, self.th)?),
            _ => None,
        };
        let x: Vec<f64> = known.iter().map(|k| {
            let un: Vec<&String> = b.doors.get(&k.key).map(|c| c.targets.iter().filter(|t| !rs.contains(t)).collect()).unwrap_or_default();
            if un.is_empty() {
                return f64::NEG_INFINITY;
            }
            match (&pr, self.mode.as_str()) {
                (_, "narrow") => -(un.len() as f64),
                (Some(pr), _) => un.iter().map(|t| pr.get(*t).copied().unwrap_or(0.0)).sum::<f64>() / un.len() as f64,
                _ => 0.0,
            }
        }).collect();
        // known is P-sorted (ties by key): its index is the P rank; X rank ties by P order
        let mut ix: Vec<usize> = (0..known.len()).collect();
        ix.sort_by(|&a, &b| x[b].total_cmp(&x[a]).then(a.cmp(&b)));
        let mut rx = vec![0usize; known.len()];
        for (r, &i) in ix.iter().enumerate() {
            rx[i] = r + 1;
        }
        let mut v: Vec<(usize, f64)> = (0..known.len()).map(|i| (i, 1.0 / (61.0 + i as f64) + 1.0 / (60.0 + rx[i] as f64))).collect();
        v.sort_by(|a, b| b.1.total_cmp(&a.1).then(a.0.cmp(&b.0)));
        Ok(v.into_iter().map(|(i, s)| Ranked { key: known[i].key.clone(), score: Some(s) }).collect())
    }
}

struct Replay {
    p: HashMap<String, f64>,
    unknown: usize,
    seen: HashSet<String>,
}

impl Decider for Replay {
    fn name(&self) -> String {
        "replay".into()
    }
    fn rank(&mut self, b: &Batch) -> avalanche::Result<Vec<Ranked>> {
        let mut v = vec![];
        for k in b.doors.keys() {
            match self.p.get(k) {
                Some(s) => v.push((k.clone(), *s)),
                None => {
                    if self.seen.insert(k.clone()) {
                        self.unknown += 1;
                    }
                }
            }
        }
        v.sort_by(|a, b| b.1.total_cmp(&a.1).then(a.0.cmp(&b.0)));
        Ok(v.into_iter().map(|(key, s)| Ranked { key, score: Some(s) }).collect())
    }
}

pub fn run<'a>(dir: &std::path::Path, g: &mut Graph<'a>, g2: &mut Graph<'a>, ft: &FullText, traces: &str, out: &str) -> avalanche::Result<()> {
    let docs = g2.docs();
    let fuse: Option<Vec<String>> = std::env::var("E2E_FUSE").ok().map(|v| v.split(',').map(String::from).collect());
    let th: (f64, f64) = std::env::var("E2E_THETA").ok().map(|v| { let x: Vec<f64> = v.split(',').map(|y| y.trim().parse().unwrap()).collect(); (x[0], x[1]) }).unwrap_or((-1.0, 0.0));
    let mut real = Edges { lk: Links { cache: HashMap::new(), shuffle: None }, cache: HashMap::new() };
    let mut shuf = Edges { lk: Links { cache: HashMap::new(), shuffle: Some(&docs) }, cache: HashMap::new() };
    let mut d6 = D6::new(dir);
    let mut f = std::fs::File::create(out)?;
    let orders: Vec<String> = std::env::var("E2E_ORDERS").unwrap_or_else(|_| "rank,per_target".into()).split(',').map(String::from).collect();
    for line in std::fs::read_to_string(traces)?.lines().filter(|l| !l.trim().is_empty()) {
        let row: serde_json::Value = serde_json::from_str(line)?;
        let w = &row["walk"];
        let question = w["question"].as_str().unwrap().to_string();
        let mut p: HashMap<String, f64> = HashMap::new();
        for b in w["trace"]["batches"].as_array().unwrap() {
            for r in b["ranking"].as_array().unwrap() {
                if let Some(s) = r["score"].as_f64() {
                    p.insert(r["key"].as_str().unwrap().to_string(), s);
                }
            }
        }
        let recorded: Vec<String> = w["documents"].as_array().unwrap().iter().map(|d| d["id"].as_str().unwrap().to_string()).collect();
        let order: Vec<String> = ft.search(&question).into_iter().map(|h| h.0).collect();
        let mut arms = serde_json::Map::new();
        for o in fuse.as_ref().unwrap_or(&orders) {
            let st: Settings = serde_json::from_value(serde_json::json!({"waves": 10, "seeds": 5, "wave": 1_000_000, "per_wave": 0,
                "open": 1, "max_reads": 10, "fill": false, "within": "shown", "cap": 100, "order": if fuse.is_some() { "rank" } else { o.as_str() }}))?;
            let r = Replay { p: p.clone(), unknown: 0, seen: HashSet::new() };
            let mut fz = Fused { r, mode: o.clone(), th: if o == "learned" { th } else { (-1.0, 0.0) }, g: &mut *g2, real: &mut real, shuf: &mut shuf };
            let wk = walk(g, order.clone(), st, &question, &mut fz, &mut d6)?;
            let dec = &fz.r;
            let reads: Vec<serde_json::Value> = wk.reads.iter().take(10).map(|r| serde_json::json!([r.doc, r.via.clone().unwrap_or_default(), r.wave])).collect();
            let opened: Vec<serde_json::Value> = wk.batches.iter().flat_map(|b| b.opened.iter()).map(|k| {
                let c = wk.clues.get(k);
                serde_json::json!({"key": k, "p": p.get(k), "width": c.map(|c| c.targets.len())})
            }).collect();
            arms.insert(o.clone(), serde_json::json!({"reads": reads, "opened": opened, "unknown": dec.unknown}));
        }
        let out_row = serde_json::json!({"qid": row["qid"], "gold": row["gold"], "recorded": recorded,
            "search": order.iter().take(10).collect::<Vec<_>>(), "arms": arms});
        writeln!(f, "{out_row}")?;
    }
    Ok(())
}
