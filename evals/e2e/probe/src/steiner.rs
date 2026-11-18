//! evals/steiner/REGISTERED.md (a): the Steiner cost. From search's 5 seeds, through the walk's own doors, reaching
//! target x through door d costs x's place among d's unread targets in shown order. Per gold, the cheapest path of 1 or
//! 2 doors; per question, a greedy cover (cheapest remaining gold first, its path's reads added) as an upper bound.
//! Controls: 5 random seeds, and doors whose targets are drawn at random at the same width. Also, for (b), each
//! recorded batch door's search-order score (its best target's search rank). $0, no decider.
use std::collections::{HashMap, HashSet};
use std::io::Write;

use avalanche::walk::d6::{doors_of, D6};
use avalanche::walk::lab::Graph;
use avalanche::walk::text::FullText;

const CAP: usize = 100;
const MAX_READS: usize = 60;

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

/// The doors a document raises, each as its targets in shown order (or, shuffled, random docs at the same width).
struct Doors<'a> {
    d6: &'a mut D6,
    cache: HashMap<String, Vec<Vec<String>>>,
    shuffle: Option<(String, &'a [String])>,
}

impl Doors<'_> {
    fn of(&mut self, g: &mut Graph, x: &str) -> avalanche::Result<Vec<Vec<String>>> {
        if let Some(v) = self.cache.get(x) {
            return Ok(v.clone());
        }
        let mut out = vec![];
        for c in doors_of(g, x, CAP)? {
            match &self.shuffle {
                Some((qid, docs)) => {
                    let mut r = Rng::new(&format!("{qid}:{}", c.key));
                    out.push((0..c.targets.len()).map(|_| docs[(r.next() % docs.len() as u64) as usize].clone()).collect());
                }
                None => out.push(self.d6.shown_order(&c, g)?),
            }
        }
        self.cache.insert(x.to_string(), out.clone());
        Ok(out)
    }
}

/// Cost to `x` (reads, counting x) from what is read, through one door of a read document; with the path's reads.
fn one_hop(g: &mut Graph, dr: &mut Doors, read: &[String], rs: &HashSet<String>) -> avalanche::Result<HashMap<String, (usize, Vec<String>)>> {
    let mut best: HashMap<String, (usize, Vec<String>)> = HashMap::new();
    for r in read {
        for door in dr.of(g, r)? {
            let mut path: Vec<String> = vec![];
            for d in door {
                if rs.contains(&d) || path.contains(&d) {
                    continue;
                }
                path.push(d.clone());
                if path.len() > MAX_READS {
                    break;
                }
                let c = path.len();
                if best.get(&d).is_none_or(|b| c < b.0) {
                    best.insert(d, (c, path.clone()));
                }
            }
        }
    }
    Ok(best)
}

/// Greedy cover of the gold from the seeds: (each gold's read count at arrival or None, total reads, first gold's
/// cost alone, each gold's own cheapest cost from the seeds).
fn cover(g: &mut Graph, dr: &mut Doors, seeds: &[String], gold: &[String]) -> avalanche::Result<serde_json::Value> {
    let mut read: Vec<String> = seeds.to_vec();
    let mut rs: HashSet<String> = read.iter().cloned().collect();
    let mut arrival: HashMap<String, usize> = gold.iter().filter(|x| rs.contains(*x)).map(|x| (x.clone(), 0)).collect();
    let mut alone: HashMap<String, Option<usize>> = HashMap::new();
    let mut first = true;
    loop {
        let left: Vec<&String> = gold.iter().filter(|x| !rs.contains(*x)).collect();
        if left.is_empty() || read.len() - seeds.len() >= MAX_READS {
            break;
        }
        let h1 = one_hop(g, dr, &read, &rs)?;
        let mut pick: Option<(usize, Vec<String>, String)> = None;
        for gd in &left {
            let mut c: Option<(usize, Vec<String>)> = h1.get(*gd).cloned();
            // two doors: through y, a target one door away, then a door of y
            let mut ys: Vec<(&String, &(usize, Vec<String>))> = h1.iter().filter(|(_, v)| v.0 < c.as_ref().map(|c| c.0).unwrap_or(MAX_READS)).collect();
            ys.sort_by_key(|(y, v)| (v.0, (*y).clone()));
            for (y, (cy, py)) in ys {
                if c.as_ref().is_some_and(|c| *cy + 1 >= c.0) {
                    break;
                }
                let mut seen: HashSet<String> = rs.clone();
                seen.extend(py.iter().cloned());
                for door in dr.of(g, y)? {
                    let mut path = py.clone();
                    for d in door {
                        if seen.contains(&d) || path.contains(&d) {
                            continue;
                        }
                        path.push(d.clone());
                        if &d == *gd {
                            if c.as_ref().is_none_or(|c| path.len() < c.0) {
                                c = Some((path.len(), path.clone()));
                            }
                            break;
                        }
                        if c.as_ref().is_some_and(|c| path.len() >= c.0) {
                            break;
                        }
                    }
                }
            }
            if first {
                alone.insert((*gd).clone(), c.as_ref().map(|c| c.0));
            }
            if let Some((n, p)) = c {
                if pick.as_ref().is_none_or(|b| n < b.0) {
                    pick = Some((n, p, (*gd).clone()));
                }
            }
        }
        first = false;
        let Some((_, path, _)) = pick else { break };
        for d in path {
            if rs.insert(d.clone()) {
                read.push(d.clone());
                if gold.contains(&d) {
                    arrival.insert(d, read.len() - seeds.len());
                }
            }
        }
    }
    let costs: Vec<Option<usize>> = gold.iter().map(|x| arrival.get(x).copied()).collect();
    let all = if costs.iter().all(|c| c.is_some()) { costs.iter().map(|c| c.unwrap()).max() } else { None };
    let alone: Vec<Option<usize>> = gold.iter().map(|x| if seeds.contains(x) { Some(0) } else { alone.get(x).copied().flatten() }).collect();
    Ok(serde_json::json!({"arrival": costs, "all": all, "alone": alone}))
}

pub fn run(dir: &std::path::Path, g: &mut Graph, ft: &FullText, traces: &str, out: &str) -> avalanche::Result<()> {
    let docs = g.docs();
    let mut d6 = D6::new(dir);
    let mut real_cache: HashMap<String, Vec<Vec<String>>> = HashMap::new();
    let mut f = std::fs::File::create(out)?;
    for line in std::fs::read_to_string(traces)?.lines().filter(|l| !l.trim().is_empty()) {
        let row: serde_json::Value = serde_json::from_str(line)?;
        let qid = row["qid"].as_str().unwrap().to_string();
        let w = &row["walk"];
        let question = w["question"].as_str().unwrap();
        let gold: Vec<String> = match &row["gold"] {
            serde_json::Value::Array(v) => v.iter().filter_map(|x| x.as_str().map(String::from)).collect(),
            serde_json::Value::Object(m) => m.keys().cloned().collect(),
            _ => vec![],
        };
        let gold: Vec<String> = gold.into_iter().filter(|d| g.holds(d)).collect();
        let order: Vec<String> = ft.search(question).into_iter().map(|h| h.0).collect();
        let rank: HashMap<&str, usize> = order.iter().enumerate().map(|(i, d)| (d.as_str(), i + 1)).collect();
        let seeds: Vec<String> = order.iter().take(5).cloned().collect();
        let real = {
            let mut dr = Doors { d6: &mut d6, cache: std::mem::take(&mut real_cache), shuffle: None };
            let v = cover(g, &mut dr, &seeds, &gold)?;
            real_cache = dr.cache;
            v
        };
        let mut rng = Rng::new(&qid);
        let rseeds: Vec<String> = (0..5).map(|_| docs[(rng.next() % docs.len() as u64) as usize].clone()).collect();
        let random = {
            let mut dr = Doors { d6: &mut d6, cache: std::mem::take(&mut real_cache), shuffle: None };
            let v = cover(g, &mut dr, &rseeds, &gold)?;
            real_cache = dr.cache;
            v
        };
        let shuffled = {
            let mut dr = Doors { d6: &mut d6, cache: HashMap::new(), shuffle: Some((qid.clone(), &docs)) };
            cover(g, &mut dr, &seeds, &gold)?
        };
        // (b)'s search-order control: each recorded batch door's best target's search rank
        let mut so = serde_json::Map::new();
        for b in w["trace"]["batches"].as_array().unwrap() {
            for d in b["doors"].as_array().unwrap() {
                let best = d["targets"].as_array().unwrap().iter().filter_map(|t| rank.get(t.as_str().unwrap()).copied()).min();
                so.insert(d["key"].as_str().unwrap().to_string(), serde_json::json!(best));
            }
        }
        let out_row = serde_json::json!({"qid": qid, "gold": gold, "seeds": seeds,
            "search_rank": gold.iter().map(|x| rank.get(x.as_str()).copied()).collect::<Vec<_>>(),
            "real": real, "random_seeds": random, "shuffled": shuffled, "search_order": so});
        writeln!(f, "{out_row}")?;
        eprintln!("{qid}");
    }
    Ok(())
}
