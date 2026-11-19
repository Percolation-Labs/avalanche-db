//! evals/predict/REGISTERED-S5.md: per question, the seeds' one-door neighbourhood H, its spectral gap (λ2 of the
//! normalized Laplacian), seed coherence, density and the gold set's conductance; and whether the recorded walk read gold
//! beyond the seeds. $0.
use std::collections::{HashMap, HashSet};
use std::io::Write;

use avalanche::walk::lab::Graph;
use avalanche::walk::text::FullText;

use crate::features::{Links, Rng};

const CAP_H: usize = 3000;
const ITERS: usize = 1000;

fn lambda2(adj: &[Vec<usize>], seed: &str) -> f64 {
    let n = adj.len();
    let d: Vec<f64> = adj.iter().map(|a| a.len() as f64).collect();
    let live: Vec<usize> = (0..n).filter(|&i| d[i] > 0.0).collect();
    if live.len() < 3 {
        return 0.0;
    }
    let sq: Vec<f64> = d.iter().map(|x| x.sqrt()).collect();
    let norm1: f64 = sq.iter().map(|x| x * x).sum::<f64>().sqrt();
    let v1: Vec<f64> = sq.iter().map(|x| x / norm1).collect();
    let mut r = Rng::new(seed);
    let mut x: Vec<f64> = (0..n).map(|i| if d[i] > 0.0 { (r.next() % 10_000) as f64 / 10_000.0 - 0.5 } else { 0.0 }).collect();
    let mut nu = 0.0;
    for _ in 0..ITERS {
        let dot: f64 = x.iter().zip(&v1).map(|(a, b)| a * b).sum();
        for i in 0..n {
            x[i] -= dot * v1[i];
        }
        let nx: f64 = x.iter().map(|a| a * a).sum::<f64>().sqrt();
        if nx == 0.0 {
            return 0.0;
        }
        for v in x.iter_mut() {
            *v /= nx;
        }
        // y = (I + D^-1/2 A D^-1/2) x / 2
        let mut y = vec![0.0; n];
        for i in 0..n {
            if d[i] == 0.0 {
                continue;
            }
            let mut s = 0.0;
            for &j in &adj[i] {
                s += x[j] / sq[j];
            }
            y[i] = 0.5 * x[i] + 0.5 * s / sq[i];
        }
        nu = y.iter().zip(&x).map(|(a, b)| a * b).sum();
        x = y;
    }
    // ν = (1 + μ2) / 2 and λ2 = 1 − μ2
    (2.0 * (1.0 - nu)).max(0.0)
}

pub fn run(g: &mut Graph, ft: &FullText, traces: &str, out: &str) -> avalanche::Result<()> {
    let mut lk = Links { cache: HashMap::new(), shuffle: None };
    let mut f = std::fs::File::create(out)?;
    for line in std::fs::read_to_string(traces)?.lines().filter(|l| !l.trim().is_empty()) {
        let row: serde_json::Value = serde_json::from_str(line)?;
        let qid = row["qid"].as_str().unwrap().to_string();
        let w = &row["walk"];
        let gold: HashSet<String> = match &row["gold"] {
            serde_json::Value::Array(v) => v.iter().filter_map(|x| x.as_str().map(String::from)).collect(),
            serde_json::Value::Object(m) => m.keys().cloned().collect(),
            _ => HashSet::new(),
        };
        let order: Vec<String> = ft.search(w["question"].as_str().unwrap()).into_iter().map(|h| h.0).collect();
        let seeds: Vec<String> = order.iter().take(5).cloned().collect();
        let mut nodes: Vec<String> = seeds.clone();
        let mut idx: HashMap<String, usize> = seeds.iter().enumerate().map(|(i, s)| (s.clone(), i)).collect();
        let mut nb: Vec<HashSet<String>> = vec![];
        for s in &seeds {
            let mut m = HashSet::new();
            for (_, tg) in lk.of(g, s)?.iter() {
                for t in tg {
                    m.insert(t.clone());
                    if !idx.contains_key(t) && nodes.len() < CAP_H {
                        idx.insert(t.clone(), nodes.len());
                        nodes.push(t.clone());
                    }
                }
            }
            nb.push(m);
        }
        let mut adj: Vec<HashSet<usize>> = vec![HashSet::new(); nodes.len()];
        for i in 0..nodes.len() {
            let u = nodes[i].clone();
            for (_, tg) in lk.of(g, &u)?.iter() {
                for t in tg {
                    if let Some(&j) = idx.get(t) {
                        if j != i {
                            adj[i].insert(j);
                            adj[j].insert(i);
                        }
                    }
                }
            }
        }
        let adj: Vec<Vec<usize>> = adj.into_iter().map(|s| { let mut v: Vec<usize> = s.into_iter().collect(); v.sort(); v }).collect();
        let m: usize = adj.iter().map(|a| a.len()).sum::<usize>() / 2;
        let mut jac = vec![];
        for a in 0..nb.len() {
            for b in a + 1..nb.len() {
                let u = nb[a].union(&nb[b]).count();
                jac.push(if u == 0 { 0.0 } else { nb[a].intersection(&nb[b]).count() as f64 / u as f64 });
            }
        }
        let gs: HashSet<usize> = nodes.iter().enumerate().filter(|(_, d)| gold.contains(*d)).map(|(i, _)| i).collect();
        let (mut cut, mut vol) = (0usize, 0usize);
        for &i in &gs {
            vol += adj[i].len();
            cut += adj[i].iter().filter(|j| !gs.contains(j)).count();
        }
        let vol_rest = 2 * m - vol;
        let cond = if gs.is_empty() || vol == 0 || vol_rest == 0 { None } else { Some(cut as f64 / vol.min(vol_rest) as f64) };
        let beyond = w["documents"].as_array().unwrap().iter().any(|d| d["wave"].as_u64().unwrap_or(0) > 0 && gold.contains(d["id"].as_str().unwrap()));
        let l2 = lambda2(&adj, &qid);
        writeln!(f, "{}", serde_json::json!({"qid": qid, "n": nodes.len(), "edges": m, "gap": l2,
            "coherence": if jac.is_empty() { 0.0 } else { jac.iter().sum::<f64>() / jac.len() as f64 },
            "density": if nodes.is_empty() { 0.0 } else { m as f64 / nodes.len() as f64 },
            "gold_in_h": gs.len(), "gold_conductance": cond, "walk_gold_beyond_seeds": beyond}))?;
        eprintln!("{qid} n {} gap {l2:.4}", nodes.len());
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::lambda2;

    fn clique(n: usize, off: usize, adj: &mut Vec<Vec<usize>>) {
        for i in 0..n {
            for j in 0..n {
                if i != j {
                    adj[off + i].push(off + j);
                }
            }
        }
    }

    #[test]
    fn known_gaps() {
        // K10: normalized Laplacian eigenvalues 0 and n/(n-1)
        let mut a = vec![vec![]; 10];
        clique(10, 0, &mut a);
        assert!((lambda2(&a, "k") - 10.0 / 9.0).abs() < 1e-3, "{}", lambda2(&a, "k"));
        // two K10 joined by one edge: a small gap; disjoint: zero
        let mut b = vec![vec![]; 20];
        clique(10, 0, &mut b);
        clique(10, 10, &mut b);
        let z = lambda2(&b, "z");
        assert!(z < 1e-3, "{z}");
        b[0].push(10);
        b[10].push(0);
        let s = lambda2(&b, "s");
        assert!(s > 1e-3 && s < 0.05, "{s}");
    }
}
