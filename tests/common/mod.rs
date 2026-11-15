//! A synthetic lab graph and a fixed P for the door tests: deterministic, so a walk on it can be held to a golden
//! file captured from the engine before the decider refactor.
#![allow(dead_code)]

use std::collections::BTreeMap;

use avalanche::store::Store;
use sha2::{Digest, Sha256};

pub const CONV: &str = "syn";
pub const DOCS: usize = 400;

fn h(s: &str) -> u64 {
    let d = Sha256::digest(s.as_bytes());
    u64::from_be_bytes(d[..8].try_into().unwrap())
}

pub fn doc(i: usize) -> String {
    format!("d{i:03}")
}

/// P for a door: a fixed number in [0, 1) from its key, so the walk does not depend on anything outside this file.
pub fn p_of(key: &str) -> f64 {
    (h(key) % 1000) as f64 / 1000.0
}

/// 400 documents; each holds 2-4 of 120 terms (term j is held more often for small j, so df varies), sits beside
/// its neighbours in id order, and is near three others chosen by hash.
pub fn graph_line() -> String {
    let mut keys = BTreeMap::new();
    let mut terms: BTreeMap<String, Vec<String>> = BTreeMap::new();
    let mut beside: BTreeMap<String, Vec<String>> = BTreeMap::new();
    let mut near: BTreeMap<String, Vec<String>> = BTreeMap::new();
    for i in 0..DOCS {
        let d = doc(i);
        keys.insert(d.clone(), d.clone());
        let n = 2 + (h(&format!("n{i}")) % 3) as usize;
        let mut ts: Vec<String> = (0..n).map(|k| {
            let r = h(&format!("t{i}.{k}")) % 10_000;
            let j = ((r as f64 / 10_000.0).powi(2) * 120.0) as usize;
            format!("w{j}")
        }).collect();
        ts.sort();
        ts.dedup();
        terms.insert(d.clone(), ts);
        let mut b = vec![];
        if i > 0 { b.push(doc(i - 1)); }
        if i + 1 < DOCS { b.push(doc(i + 1)); }
        beside.insert(d.clone(), b);
        near.insert(d.clone(), (0..3).map(|k| doc((h(&format!("near{i}.{k}")) % DOCS as u64) as usize)).filter(|x| *x != d).collect());
    }
    let mut post: BTreeMap<String, Vec<String>> = BTreeMap::new();
    for (d, ts) in &terms {
        for t in ts {
            post.entry(t.clone()).or_default().push(d.clone());
        }
    }
    serde_json::json!({"conv": CONV, "graph": {"keys": keys, "terms": terms, "post": post, "beside": beside, "near": near}}).to_string()
}

/// A fresh store holding the synthetic graph.
pub fn store(name: &str) -> (Store, std::path::PathBuf) {
    let dir = std::env::temp_dir().join(format!("ava-doors-{name}-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&dir);
    std::fs::create_dir_all(&dir).unwrap();
    let g = dir.join("graphs.jsonl");
    std::fs::write(&g, graph_line() + "\n").unwrap();
    let s = Store::open(dir.join("s.redb")).unwrap();
    avalanche::construct::lab::import(&s, &g, None).unwrap();
    (s, dir)
}

/// Search's order for question q: every document, in a hash order of its own.
pub fn order(q: usize) -> Vec<String> {
    let mut v: Vec<String> = (0..DOCS).map(doc).collect();
    v.sort_by_key(|d| h(&format!("q{q}:{d}")));
    v
}

/// The settings the golden file was captured under: (name, settings JSON).
pub fn cases() -> Vec<(String, usize, serde_json::Value)> {
    let mut out = vec![];
    for q in 0..4 {
        for order in ["per_target", "p", "convergence"] {
            out.push((format!("q{q}-{order}"), q, serde_json::json!({"waves": 6, "wave": 20, "seeds": 5, "per_wave": 5, "cap": 30, "gate": 0.5, "order": order})));
        }
    }
    out
}
