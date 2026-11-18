//! evals/structural/REGISTERED.md: question-free structural properties of each door at each recorded wave (width,
//! cohesion, convergence, local PPR mass from what is read), on the real links and on links shuffled at the same
//! widths; and per question, PPR from the seeds onto the gold, with random-seed and shuffled controls. $0.
use std::collections::{HashMap, HashSet, VecDeque};
use std::io::Write;

use avalanche::walk::d6::doors_of;
use avalanche::walk::lab::Graph;
use avalanche::walk::text::FullText;

const CAP: usize = 100;
const ALPHA: f64 = 0.15;
const EPS: f64 = 1e-4;
const COH: usize = 30;

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

/// A passage's doors as (key, targets); shuffled: each door keeps its key and width, its targets drawn at random.
struct Links<'a> {
    cache: HashMap<String, std::rc::Rc<Vec<(String, Vec<String>)>>>,
    shuffle: Option<&'a [String]>,
}

impl Links<'_> {
    fn of(&mut self, g: &mut Graph, x: &str) -> avalanche::Result<std::rc::Rc<Vec<(String, Vec<String>)>>> {
        if let Some(v) = self.cache.get(x) {
            return Ok(v.clone());
        }
        let mut out = vec![];
        if g.holds(x) {
            for c in doors_of(g, x, CAP)? {
                let tg = match self.shuffle {
                    Some(docs) => {
                        let mut r = Rng::new(&format!("{x}|{}", c.key));
                        (0..c.targets.len()).map(|_| docs[(r.next() % docs.len() as u64) as usize].clone()).collect()
                    }
                    None => c.targets,
                };
                out.push((c.key, tg));
            }
        }
        let v = std::rc::Rc::new(out);
        self.cache.insert(x.to_string(), v.clone());
        Ok(v)
    }
}

/// Personalized PageRank from `from` (uniform), push to residual EPS: doc -> a door uniformly -> a target uniformly.
fn ppr(g: &mut Graph, lk: &mut Links, from: &[String]) -> avalanche::Result<HashMap<String, f64>> {
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
        let doors = lk.of(g, &u)?;
        let doors: Vec<&(String, Vec<String>)> = doors.iter().filter(|d| !d.1.is_empty()).collect();
        if doors.is_empty() {
            *p.entry(u.clone()).or_default() += (1.0 - ALPHA) * ru;
            continue;
        }
        let share = (1.0 - ALPHA) * ru / doors.len() as f64;
        for (_, tg) in doors {
            let each = share / tg.len() as f64;
            for t in tg {
                let e = r.entry(t.clone()).or_default();
                let was = *e;
                *e += each;
                if was < EPS && *e >= EPS {
                    q.push_back(t.clone());
                }
            }
        }
    }
    Ok(p)
}

/// target -> (how many of a's doors list it, one of their keys)
fn nbrs<'c>(g: &mut Graph, lk: &mut Links, nb: &'c mut HashMap<String, HashMap<String, (usize, String)>>, a: &str) -> avalanche::Result<&'c HashMap<String, (usize, String)>> {
    if !nb.contains_key(a) {
        let mut m: HashMap<String, (usize, String)> = HashMap::new();
        for (k, tg) in lk.of(g, a)?.iter() {
            for t in tg {
                let e = m.entry(t.clone()).or_insert((0, k.clone()));
                e.0 += 1;
            }
        }
        nb.insert(a.to_string(), m);
    }
    Ok(&nb[a])
}

fn linked(g: &mut Graph, lk: &mut Links, nb: &mut HashMap<String, HashMap<String, (usize, String)>>, a: &str, b: &str, not_key: &str) -> avalanche::Result<bool> {
    Ok(nbrs(g, lk, nb, a)?.get(b).is_some_and(|(n, k)| *n > 1 || k != not_key))
}

fn props(g: &mut Graph, lk: &mut Links, nb: &mut HashMap<String, HashMap<String, (usize, String)>>, read: &[String], doors: &[(String, String, Vec<String>)]) -> avalanche::Result<Vec<serde_json::Value>> {
    let pr = ppr(g, lk, read)?;
    // who links to what, from the read set (convergence)
    let mut into: HashMap<String, HashSet<String>> = HashMap::new();
    for r in read {
        for (_, tg) in lk.of(g, r)?.iter() {
            for t in tg {
                into.entry(t.clone()).or_default().insert(r.clone());
            }
        }
    }
    let mut out = vec![];
    for (key, source, tg) in doors {
        let mut s: Vec<&String> = tg.iter().collect();
        s.sort();
        s.truncate(COH);
        let (mut pairs, mut hit) = (0usize, 0usize);
        for i in 0..s.len() {
            for j in i + 1..s.len() {
                pairs += 1;
                if linked(g, lk, nb, s[i], s[j], key)? || linked(g, lk, nb, s[j], s[i], key)? {
                    hit += 1;
                }
            }
        }
        let mut conv: HashSet<&String> = HashSet::new();
        for t in tg {
            if let Some(v) = into.get(t) {
                conv.extend(v.iter().filter(|r| *r != source));
            }
        }
        let mass: f64 = tg.iter().map(|t| pr.get(t).copied().unwrap_or(0.0)).sum();
        out.push(serde_json::json!({"cohesion": if pairs > 0 { Some(hit as f64 / pairs as f64) } else { None },
            "convergence": conv.len(), "ppr": mass, "ppr_mean": if tg.is_empty() { 0.0 } else { mass / tg.len() as f64 }}));
    }
    Ok(out)
}

pub fn run(g: &mut Graph, ft: &FullText, traces: &str, out: &str) -> avalanche::Result<()> {
    let docs = g.docs();
    let mut real = Links { cache: HashMap::new(), shuffle: None };
    let mut shuf = Links { cache: HashMap::new(), shuffle: Some(&docs) };
    let (mut nbr, mut nbs) = (HashMap::new(), HashMap::new());
    let mut f = std::fs::File::create(out)?;
    let mut fq = std::fs::File::create(format!("{out}.questions.jsonl"))?;
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
        let rank: HashMap<&str, usize> = order.iter().enumerate().map(|(i, d)| (d.as_str(), i + 1)).collect();
        let reads = w["trace"]["reads"].as_array().unwrap();
        for b in w["trace"]["batches"].as_array().unwrap() {
            let wave = b["wave"].as_u64().unwrap();
            let read: Vec<String> = reads.iter().filter(|r| r["wave"].as_u64().unwrap() < wave).map(|r| r["doc"].as_str().unwrap().to_string()).collect();
            let rs: HashSet<&String> = read.iter().collect();
            let p: HashMap<&str, (usize, Option<f64>)> = b["ranking"].as_array().unwrap().iter().enumerate()
                .map(|(i, x)| (x["key"].as_str().unwrap(), (i + 1, x["score"].as_f64()))).collect();
            let doors: Vec<(String, String, Vec<String>)> = b["doors"].as_array().unwrap().iter().map(|d| {
                let tg: Vec<String> = d["targets"].as_array().unwrap().iter().map(|t| t.as_str().unwrap().to_string()).filter(|t| !rs.contains(t)).collect();
                let key = d["key"].as_str().unwrap().to_string();
                let src = key.split_once(':').map(|(_, s)| s.to_string()).unwrap_or_default();
                (key, src, tg)
            }).filter(|d| !d.2.is_empty()).collect();
            if !doors.iter().any(|d| d.2.iter().any(|t| gold.contains(t))) {
                continue;
            }
            let pr = props(g, &mut real, &mut nbr, &read, &doors)?;
            let ps = props(g, &mut shuf, &mut nbs, &read, &doors)?;
            for ((d, a), s) in doors.iter().zip(pr).zip(ps) {
                let (rk, sc) = p.get(d.0.as_str()).copied().unwrap_or((usize::MAX, None));
                let so = d.2.iter().filter_map(|t| rank.get(t.as_str()).copied()).min();
                let kind = d.0.split(':').next().unwrap_or("");
                writeln!(f, "{}", serde_json::json!({"qid": qid, "wave": wave, "key": d.0, "kind": kind, "width": d.2.len(),
                    "gold": d.2.iter().filter(|t| gold.contains(*t)).count(), "p": sc, "rank": if rk == usize::MAX { None } else { Some(rk) },
                    "search_rank": so, "real": a, "shuffled": s}))?;
            }
        }
        // per question: PPR from the seeds onto the gold, with controls
        let seeds: Vec<String> = order.iter().take(5).cloned().collect();
        let mut rng = Rng::new(&qid);
        let rseeds: Vec<String> = (0..5).map(|_| docs[(rng.next() % docs.len() as u64) as usize].clone()).collect();
        let mut q = serde_json::Map::new();
        for (name, sd) in [("real", &seeds), ("random_seeds", &rseeds)] {
            let pr = ppr(g, &mut real, sd)?;
            q.insert(name.into(), gold_mass(&pr, &gold, sd));
        }
        let pr = ppr(g, &mut shuf, &seeds)?;
        q.insert("shuffled".into(), gold_mass(&pr, &gold, &seeds));
        writeln!(fq, "{}", serde_json::json!({"qid": qid, "ppr": q}))?;
        eprintln!("{qid}");
    }
    Ok(())
}

fn gold_mass(pr: &HashMap<String, f64>, gold: &HashSet<String>, seeds: &[String]) -> serde_json::Value {
    let mut v: Vec<(&String, f64)> = pr.iter().filter(|(d, _)| !seeds.contains(d)).map(|(d, x)| (d, *x)).collect();
    v.sort_by(|a, b| b.1.total_cmp(&a.1));
    let best = v.iter().position(|(d, _)| gold.contains(*d)).map(|i| i + 1);
    let mass: f64 = v.iter().filter(|(d, _)| gold.contains(*d)).map(|x| x.1).sum();
    serde_json::json!({"gold_mass": mass, "best_gold_rank": best, "support": v.len()})
}
