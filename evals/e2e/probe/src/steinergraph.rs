//! evals/steinergraph/REGISTERED-P1.md: predict a question's Steiner graph from the question and its seeds. Per question,
//! the top-20 non-seed passages under search (S), the uniform avalanche (U), the question-aware avalanche (Q) and Q on
//! shuffled links; the best gold rank under each; and the avalanche wave by wave (1–3 steps, no restart). $0.
use std::collections::{HashMap, HashSet, VecDeque};
use std::io::Write;

use avalanche::walk::lab::Graph;
use avalanche::walk::text::FullText;

use crate::features::Links;
use crate::votes::Edges;

const ALPHA: f64 = 0.15;
const EPS: f64 = 1e-4;
const FLOOR: f64 = 0.01;
const PRUNE: f64 = 1e-7;

/// Edge weight u→t through a door of ln-width lw: (1/width) · (s(t) + FLOOR) when `s` is given, else 1/width.
fn wt(lw: f64, t: &str, s: Option<&HashMap<String, f64>>) -> f64 {
    let base = (-lw).exp();
    match s {
        Some(s) => base * (s.get(t).copied().unwrap_or(0.0) + FLOOR),
        None => base,
    }
}

fn ppr(g: &mut Graph, e: &mut Edges, from: &[String], s: Option<&HashMap<String, f64>>) -> avalanche::Result<HashMap<String, f64>> {
    let mut p: HashMap<String, f64> = HashMap::new();
    let mut r: HashMap<String, f64> = HashMap::new();
    let mut q: VecDeque<String> = VecDeque::new();
    for x in from {
        *r.entry(x.clone()).or_default() += 1.0 / from.len() as f64;
        q.push_back(x.clone());
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
        let w: Vec<f64> = ed.iter().map(|(t, lw, _)| wt(*lw, t, s)).collect();
        let z: f64 = w.iter().sum();
        for ((t, _, _), wi) in ed.iter().zip(&w) {
            let x = r.entry(t.clone()).or_default();
            let was = *x;
            *x += (1.0 - ALPHA) * ru * wi / z;
            if was < EPS && *x >= EPS {
                q.push_back(t.clone());
            }
        }
    }
    Ok(p)
}

/// The walk distribution after 1..=steps steps from the seeds, without restart (mass below PRUNE dropped).
fn steps(g: &mut Graph, e: &mut Edges, from: &[String], s: Option<&HashMap<String, f64>>, n: usize) -> avalanche::Result<Vec<HashMap<String, f64>>> {
    let mut x: HashMap<String, f64> = from.iter().map(|d| (d.clone(), 1.0 / from.len() as f64)).collect();
    let mut out = vec![];
    for _ in 0..n {
        let mut y: HashMap<String, f64> = HashMap::new();
        for (u, m) in &x {
            if *m < PRUNE {
                continue;
            }
            let ed = e.of(g, u)?;
            if ed.is_empty() {
                *y.entry(u.clone()).or_default() += m;
                continue;
            }
            let w: Vec<f64> = ed.iter().map(|(t, lw, _)| wt(*lw, t, s)).collect();
            let z: f64 = w.iter().sum();
            for ((t, _, _), wi) in ed.iter().zip(&w) {
                *y.entry(t.clone()).or_default() += m * wi / z;
            }
        }
        out.push(y.clone());
        x = y;
    }
    Ok(out)
}

fn ranked(m: &HashMap<String, f64>, seeds: &HashSet<&String>) -> Vec<String> {
    let mut v: Vec<(&String, f64)> = m.iter().filter(|(d, _)| !seeds.contains(d)).map(|(d, x)| (d, *x)).collect();
    v.sort_by(|a, b| b.1.total_cmp(&a.1).then(a.0.cmp(b.0)));
    v.into_iter().map(|(d, _)| d.clone()).collect()
}

fn summary(order: &[String], gold: &HashSet<String>) -> serde_json::Value {
    let best = order.iter().position(|d| gold.contains(d)).map(|i| i + 1);
    let hits = |k: usize| order.iter().take(k).filter(|d| gold.contains(*d)).count();
    serde_json::json!({"best": best, "at5": hits(5), "at10": hits(10), "at20": hits(20)})
}

pub fn run(g: &mut Graph, ft: &FullText, traces: &str, out: &str) -> avalanche::Result<()> {
    let docs = g.docs();
    let mut real = Edges { lk: Links { cache: HashMap::new(), shuffle: None }, cache: HashMap::new() };
    let mut shuf = Edges { lk: Links { cache: HashMap::new(), shuffle: Some(&docs) }, cache: HashMap::new() };
    let mut f = std::fs::File::create(out)?;
    let mut fnodes = std::fs::File::create(format!("{out}.nodes.jsonl"))?;
    for line in std::fs::read_to_string(traces)?.lines().filter(|l| !l.trim().is_empty()) {
        let row: serde_json::Value = serde_json::from_str(line)?;
        let qid = row["qid"].as_str().unwrap().to_string();
        let w = &row["walk"];
        let gold_all: HashSet<String> = match &row["gold"] {
            serde_json::Value::Array(v) => v.iter().filter_map(|x| x.as_str().map(String::from)).collect(),
            serde_json::Value::Object(m) => m.keys().cloned().collect(),
            _ => HashSet::new(),
        };
        let hits = ft.search(w["question"].as_str().unwrap());
        let top = hits.first().map(|h| h.1).unwrap_or(1.0).max(1e-9);
        let s: HashMap<String, f64> = hits.iter().map(|(d, x)| (d.clone(), x / top)).collect();
        let order: Vec<String> = hits.iter().map(|h| h.0.clone()).collect();
        let seeds: Vec<String> = order.iter().take(5).cloned().collect();
        let ss: HashSet<&String> = seeds.iter().collect();
        let gold: HashSet<String> = gold_all.iter().filter(|d| !ss.contains(d)).cloned().collect();
        let srch: Vec<String> = order.iter().skip(5).cloned().collect();
        let um = ppr(g, &mut real, &seeds, None)?;
        let qm = ppr(g, &mut real, &seeds, Some(&s))?;
        let u = ranked(&um, &ss);
        let q = ranked(&qm, &ss);
        let top = |r: &[String], m: &HashMap<String, f64>| -> serde_json::Value {
            let k: Vec<&String> = r.iter().take(200).collect();
            let z: f64 = k.iter().map(|d| m[*d]).sum::<f64>().max(1e-300);
            serde_json::Value::Array(k.iter().map(|d| serde_json::json!([d, m[*d] / z])).collect())
        };
        writeln!(fnodes, "{}", serde_json::json!({"qid": qid, "U": top(&u, &um), "Q": top(&q, &qm)}))?;
        let qs = ranked(&ppr(g, &mut shuf, &seeds, Some(&s))?, &ss);
        let mut aval = serde_json::Map::new();
        for (name, sc) in [("U", None), ("Q", Some(&s))] {
            let st = steps(g, &mut real, &seeds, sc, 3)?;
            let v: Vec<serde_json::Value> = st.iter().map(|m| {
                let mass: f64 = gold.iter().map(|d| m.get(d).copied().unwrap_or(0.0)).sum();
                let r = ranked(m, &ss);
                serde_json::json!({"gold_mass": mass, "best": r.iter().position(|d| gold.contains(d)).map(|i| i + 1), "support": m.len()})
            }).collect();
            aval.insert(name.into(), v.into());
        }
        let walk_hits = w["documents"].as_array().unwrap().iter().filter(|d| d["wave"].as_u64().unwrap_or(0) > 0 && gold.contains(d["id"].as_str().unwrap())).count();
        writeln!(f, "{}", serde_json::json!({"qid": qid, "gold_beyond": gold.len(), "walk_at5": walk_hits,
            "S": summary(&srch, &gold), "U": summary(&u, &gold), "Q": summary(&q, &gold), "Q_shuffled": summary(&qs, &gold),
            "avalanche": aval}))?;
        eprintln!("{qid}");
    }
    Ok(())
}
