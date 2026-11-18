//! evals/structure/REGISTERED.md: per question, each gold document's search rank, link distance from the seeds (0, 1,
//! 2, >2) with the kind and width of the door that reaches it, the frontier size, and how the gold connect among
//! themselves; with random seeds and shuffled links as controls. $0, no decider.
use std::collections::{BTreeMap, HashMap, HashSet};

use avalanche::walk::d6::doors_of;
use avalanche::walk::lab::Graph;
use avalanche::walk::text::FullText;

const CAP: usize = 100;

struct Rng(u64);
impl Rng {
    fn new(s: &str) -> Rng {
        let mut h: u64 = 1118;
        for b in s.bytes() {
            h = h.wrapping_mul(1099511628211).wrapping_add(b as u64);
        }
        Rng(h | 1)
    }
    fn next(&mut self) -> u64 {
        self.0 ^= self.0 << 13;
        self.0 ^= self.0 >> 7;
        self.0 ^= self.0 << 17;
        self.0
    }
}

/// doc -> (kind, width) of the narrowest door of `x` that lists it
fn links(g: &mut Graph, x: &str, cache: &mut HashMap<String, BTreeMap<String, (String, usize)>>) -> avalanche::Result<BTreeMap<String, (String, usize)>> {
    if let Some(v) = cache.get(x) {
        return Ok(v.clone());
    }
    let mut out: BTreeMap<String, (String, usize)> = BTreeMap::new();
    for c in doors_of(g, x, CAP)? {
        let w = c.targets.len();
        for d in c.targets {
            let e = out.entry(d).or_insert((c.kind.clone(), w));
            if w < e.1 {
                *e = (c.kind.clone(), w);
            }
        }
    }
    cache.insert(x.to_string(), out.clone());
    Ok(out)
}

fn frontier(g: &mut Graph, seeds: &[String], cache: &mut HashMap<String, BTreeMap<String, (String, usize)>>) -> avalanche::Result<BTreeMap<String, (String, usize)>> {
    let mut n1: BTreeMap<String, (String, usize)> = BTreeMap::new();
    for s in seeds {
        for (d, kw) in links(g, s, cache)? {
            if seeds.contains(&d) {
                continue;
            }
            let e = n1.entry(d).or_insert(kw.clone());
            if kw.1 < e.1 {
                *e = kw;
            }
        }
    }
    Ok(n1)
}

fn dist(g: &mut Graph, gd: &str, seeds: &[String], n1: &BTreeMap<String, (String, usize)>, cache: &mut HashMap<String, BTreeMap<String, (String, usize)>>) -> avalanche::Result<serde_json::Value> {
    if seeds.iter().any(|s| s == gd) {
        return Ok(serde_json::json!({"d": 0}));
    }
    if let Some((k, w)) = n1.get(gd) {
        return Ok(serde_json::json!({"d": 1, "kind": k, "width": w}));
    }
    // distance 2: some doc within 1 of the seeds is linked to the gold (links taken as undirected)
    let ng = links(g, gd, cache)?;
    let best = ng.iter().filter(|(x, _)| n1.contains_key(*x)).min_by_key(|(_, kw)| kw.1);
    Ok(match best {
        Some((_, (k, w))) => serde_json::json!({"d": 2, "kind": k, "width": w}),
        None => serde_json::json!({"d": 3}),
    })
}

pub fn run(g: &mut Graph, ft: &FullText, qpath: &str, out: &str) -> avalanche::Result<()> {
    use std::io::Write;
    let docs = g.docs();
    let nd = docs.len();
    let mut f = std::fs::File::create(out)?;
    let mut cache = HashMap::new();
    for line in std::fs::read_to_string(qpath)?.lines().filter(|l| !l.trim().is_empty()) {
        let q: serde_json::Value = serde_json::from_str(line)?;
        let qid = q["qid"].as_str().unwrap_or_default().to_string();
        let question = q["question"].as_str().unwrap_or_default();
        let gold: Vec<String> = match &q["gold"] {
            serde_json::Value::Array(v) => v.iter().filter_map(|x| x.as_str().map(String::from)).collect(),
            serde_json::Value::Object(m) => m.keys().cloned().collect(),
            _ => vec![],
        };
        let gold: Vec<String> = gold.into_iter().filter(|d| g.holds(d)).collect();
        let order: Vec<String> = ft.search(question).into_iter().map(|h| h.0).collect();
        let rank: HashMap<&str, usize> = order.iter().enumerate().map(|(i, d)| (d.as_str(), i + 1)).collect();
        let seeds: Vec<String> = order.iter().take(5).cloned().collect();
        let n1 = frontier(g, &seeds, &mut cache)?;
        let mut rng = Rng::new(&qid);
        let rseeds: Vec<String> = (0..5).map(|_| docs[(rng.next() % nd as u64) as usize].clone()).collect();
        let rn1 = frontier(g, &rseeds, &mut cache)?;
        let mut per = vec![];
        for gd in &gold {
            let d = dist(g, gd, &seeds, &n1, &mut cache)?;
            let rd = dist(g, gd, &rseeds, &rn1, &mut cache)?;
            per.push(serde_json::json!({"doc": gd, "rank": rank.get(gd.as_str()), "link": d, "random_seeds": rd["d"]}));
        }
        // shuffled links, distance 1 only: each seed door keeps its width, its targets drawn at random
        let mut sh: HashSet<usize> = HashSet::new();
        let mut srng = Rng::new(&format!("shuffle:{qid}"));
        for s in &seeds {
            for c in doors_of(g, s, CAP)? {
                for _ in 0..c.targets.len() {
                    sh.insert((srng.next() % nd as u64) as usize);
                }
            }
        }
        let gi: HashSet<usize> = gold.iter().filter_map(|gd| docs.binary_search(gd).ok()).collect();
        let shuffled_d1 = gi.iter().filter(|i| sh.contains(i)).count();
        // fragments: gold pairs linked directly, and the doors that link them
        let mut pairs = vec![];
        for (i, a) in gold.iter().enumerate() {
            let la = links(g, a, &mut cache)?;
            for b in gold.iter().skip(i + 1) {
                let lb = links(g, b, &mut cache)?;
                let kw = la.get(b).or_else(|| lb.get(a)).cloned();
                pairs.push(serde_json::json!({"a": a, "b": b, "linked": kw.as_ref().map(|k| serde_json::json!({"kind": k.0, "width": k.1}))}));
            }
        }
        let row = serde_json::json!({"qid": qid, "gold": per, "frontier": n1.len(), "random_frontier": rn1.len(),
            "shuffled_frontier": sh.len(), "shuffled_d1": shuffled_d1, "pairs": pairs, "docs": nd});
        writeln!(f, "{row}")?;
        if cache.len() > 200_000 {
            cache.clear();
        }
    }
    Ok(())
}
