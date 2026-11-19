//! evals/votes/REGISTERED.md: PPR from the read set with edge weights w = exp(θ1·ln width(k) + θ2·ln(1+doors(t)))
//! for the edge u→t through door k. θ = (−1, 0) is the uniform walk (a door, then a target). For every recorded wave
//! with a gold door, each door's mass over its unread targets is written under every θ in the grid, on the real
//! links and on links shuffled at the same widths; per question, the best gold rank beyond the seeds. $0.
use std::collections::{HashMap, HashSet, VecDeque};
use std::io::Write;
use std::rc::Rc;

use avalanche::walk::lab::Graph;
use avalanche::walk::text::FullText;

use crate::features::Links;

const ALPHA: f64 = 0.15;
const EPS: f64 = 1e-4;

/// u's out-edges as (t, ln width(k), ln(1 + doors(t))), one per (door, target) pair.
pub(crate) struct Edges<'a> {
    pub(crate) lk: Links<'a>,
    pub(crate) cache: HashMap<String, Rc<Vec<(String, f64, f64)>>>,
}

impl Edges<'_> {
    fn of(&mut self, g: &mut Graph, u: &str) -> avalanche::Result<Rc<Vec<(String, f64, f64)>>> {
        if let Some(v) = self.cache.get(u) {
            return Ok(v.clone());
        }
        let doors = self.lk.of(g, u)?;
        let mut out = vec![];
        for (_, tg) in doors.iter().filter(|d| !d.1.is_empty()) {
            let lw = (tg.len() as f64).ln();
            for t in tg {
                let dt = self.lk.of(g, t)?.iter().filter(|d| !d.1.is_empty()).count();
                out.push((t.clone(), lw, (1.0 + dt as f64).ln()));
            }
        }
        let v = Rc::new(out);
        self.cache.insert(u.to_string(), v.clone());
        Ok(v)
    }
}

pub(crate) fn wppr(g: &mut Graph, e: &mut Edges, from: &[String], th: (f64, f64)) -> avalanche::Result<HashMap<String, f64>> {
    let mut p: HashMap<String, f64> = HashMap::new();
    let mut r: HashMap<String, f64> = HashMap::new();
    let mut q: VecDeque<String> = VecDeque::new();
    for s in from {
        *r.entry(s.clone()).or_default() += 1.0 / from.len() as f64;
        q.push_back(s.clone());
    }
    let mut pushes = 0usize;
    while let Some(u) = q.pop_front() {
        let ru = r.get(&u).copied().unwrap_or(0.0);
        if ru < EPS {
            continue;
        }
        pushes += 1;
        if pushes > 200_000 {
            break;
        }
        r.insert(u.clone(), 0.0);
        *p.entry(u.clone()).or_default() += ALPHA * ru;
        let ed = e.of(g, &u)?;
        if ed.is_empty() {
            *p.entry(u.clone()).or_default() += (1.0 - ALPHA) * ru;
            continue;
        }
        let w: Vec<f64> = ed.iter().map(|(_, lw, ld)| (th.0 * lw + th.1 * ld).exp()).collect();
        let z: f64 = w.iter().sum();
        for ((t, _, _), wi) in ed.iter().zip(&w) {
            let each = (1.0 - ALPHA) * ru * wi / z;
            let x = r.entry(t.clone()).or_default();
            let was = *x;
            *x += each;
            if was < EPS && *x >= EPS {
                q.push_back(t.clone());
            }
        }
    }
    Ok(p)
}

pub fn grid() -> Vec<(f64, f64)> {
    if let Ok(s) = std::env::var("E2E_THETAS") {
        return s.split(';').map(|x| {
            let v: Vec<f64> = x.split(',').map(|y| y.trim().parse().unwrap()).collect();
            (v[0], v[1])
        }).collect();
    }
    let mut v = vec![];
    for a in [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5] {
        for b in [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5] {
            v.push((a, b));
        }
    }
    v
}

pub fn run(g: &mut Graph, ft: &FullText, traces: &str, out: &str) -> avalanche::Result<()> {
    let docs = g.docs();
    let th = grid();
    let mut real = Edges { lk: Links { cache: HashMap::new(), shuffle: None }, cache: HashMap::new() };
    let mut shuf = Edges { lk: Links { cache: HashMap::new(), shuffle: Some(&docs) }, cache: HashMap::new() };
    let mut f = std::fs::File::create(out)?;
    let mut fq = std::fs::File::create(format!("{out}.questions.jsonl"))?;
    writeln!(f, "{}", serde_json::json!({"thetas": th}))?;
    for line in std::fs::read_to_string(traces)?.lines().filter(|l| !l.trim().is_empty()) {
        let row: serde_json::Value = serde_json::from_str(line)?;
        let qid = row["qid"].as_str().unwrap().to_string();
        let w = &row["walk"];
        let gold: HashSet<String> = match &row["gold"] {
            serde_json::Value::Array(v) => v.iter().filter_map(|x| x.as_str().map(String::from)).collect(),
            serde_json::Value::Object(m) => m.keys().cloned().collect(),
            _ => HashSet::new(),
        };
        let reads = w["trace"]["reads"].as_array().unwrap();
        for b in w["trace"]["batches"].as_array().unwrap() {
            let wave = b["wave"].as_u64().unwrap();
            let read: Vec<String> = reads.iter().filter(|r| r["wave"].as_u64().unwrap() < wave).map(|r| r["doc"].as_str().unwrap().to_string()).collect();
            let rs: HashSet<&String> = read.iter().collect();
            let p: HashMap<&str, Option<f64>> = b["ranking"].as_array().unwrap().iter().map(|x| (x["key"].as_str().unwrap(), x["score"].as_f64())).collect();
            let doors: Vec<(String, Vec<String>)> = b["doors"].as_array().unwrap().iter().map(|d| {
                let tg: Vec<String> = d["targets"].as_array().unwrap().iter().map(|t| t.as_str().unwrap().to_string()).filter(|t| !rs.contains(t)).collect();
                (d["key"].as_str().unwrap().to_string(), tg)
            }).filter(|d| !d.1.is_empty()).collect();
            if read.is_empty() || !doors.iter().any(|d| d.1.iter().any(|t| gold.contains(t))) {
                continue;
            }
            let mut mr: Vec<Vec<f64>> = vec![vec![]; doors.len()];
            let mut ms: Vec<Vec<f64>> = vec![vec![]; doors.len()];
            for &t in &th {
                for (e, m) in [(&mut real, &mut mr), (&mut shuf, &mut ms)] {
                    let pr = wppr(g, e, &read, t)?;
                    for (i, d) in doors.iter().enumerate() {
                        m[i].push(d.1.iter().map(|x| pr.get(x).copied().unwrap_or(0.0)).sum());
                    }
                }
            }
            for (i, d) in doors.iter().enumerate() {
                writeln!(f, "{}", serde_json::json!({"qid": qid, "wave": wave, "key": d.0, "width": d.1.len(),
                    "gold": d.1.iter().filter(|t| gold.contains(*t)).count(), "p": p.get(d.0.as_str()).copied().flatten(),
                    "real": mr[i], "shuffled": ms[i]}))?;
            }
        }
        // per question: best gold rank beyond the seeds, PPR from search's top 5
        let order: Vec<String> = ft.search(w["question"].as_str().unwrap()).into_iter().map(|h| h.0).collect();
        let seeds: Vec<String> = order.iter().take(5).cloned().collect();
        let mut best = vec![];
        for &t in &th {
            let pr = wppr(g, &mut real, &seeds, t)?;
            let mut v: Vec<(&String, f64)> = pr.iter().filter(|(d, _)| !seeds.contains(d)).map(|(d, x)| (d, *x)).collect();
            v.sort_by(|a, b| b.1.total_cmp(&a.1));
            best.push(v.iter().position(|(d, _)| gold.contains(*d)).map(|i| i + 1));
        }
        writeln!(fq, "{}", serde_json::json!({"qid": qid, "gold_beyond_seeds": gold.iter().any(|x| !seeds.contains(x)), "best_gold_rank": best}))?;
        eprintln!("{qid}");
    }
    Ok(())
}
