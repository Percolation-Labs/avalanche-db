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

pub fn run(dir: &std::path::Path, g: &mut Graph, ft: &FullText, traces: &str, out: &str) -> avalanche::Result<()> {
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
        for o in &orders {
            let st: Settings = serde_json::from_value(serde_json::json!({"waves": 10, "seeds": 5, "wave": 1_000_000, "per_wave": 0,
                "open": 1, "max_reads": 10, "fill": false, "within": "shown", "cap": 100, "order": o}))?;
            let mut dec = Replay { p: p.clone(), unknown: 0, seen: HashSet::new() };
            let wk = walk(g, order.clone(), st, &question, &mut dec, &mut d6)?;
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
