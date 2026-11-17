//! The $0 part of REGISTERED.md, on a store the `documents` adapter built: search's ranking, G0's doors (the doors
//! the three search seeds raise, as D6 shows them, each marked gold when a gold passage is behind it), and the
//! walks no model decides (oracle, width-only, coin, search-order), each cut at the first 20 reads.
//!
//!     cargo run --release -- STORE_DIR QUESTIONS.jsonl OUT.jsonl
//!
//! A question line is {qid, question, gold}; gold is a list of passage ids or a {id: hop} map.

use std::collections::{BTreeMap, HashSet};
use std::io::Write;
use std::path::Path;

use avalanche::config::Config;
use avalanche::construct::documents::Reader;
use avalanche::store::Store;
use avalanche::walk::d6::{doors_of, D6};
use avalanche::walk::doors::{Batch, Decider, Oracle, Random, Ranked, SearchOrder};
use avalanche::walk::explore::Coin;
use avalanche::walk::lab::{run, Graph, Settings};
use avalanche::walk::text::FullText;

/// Width-only: doors ranked by how many unread passages are behind them; nothing is read.
struct Width;

impl Decider for Width {
    fn name(&self) -> String {
        "width".into()
    }
    fn rank(&mut self, b: &Batch) -> avalanche::Result<Vec<Ranked>> {
        let mut v: Vec<(String, f64)> = b.doors.iter().map(|(k, c)| (k.clone(), c.targets.len() as f64)).collect();
        v.sort_by(|a, b| b.1.total_cmp(&a.1).then(a.0.cmp(&b.0)));
        Ok(v.into_iter().map(|(key, s)| Ranked { key, score: Some(s) }).collect())
    }
}

fn settings() -> Settings {
    // three seeds, then doors; reads after the first 20 are not scored
    serde_json::from_value(serde_json::json!({"seeds": 3, "wave": 10, "waves": 4, "per_wave": 0, "cap": 100})).unwrap()
}

fn main() -> avalanche::Result<()> {
    let a: Vec<String> = std::env::args().collect();
    let (dir, qpath, out) = (Path::new(&a[1]), &a[2], &a[3]);
    let cfg = Config::load(dir)?;
    let store = Store::open(Config::store_path(dir))?;
    let t = store.tenant(&cfg.tenant)?;
    let mut g = Graph::open_items(&store, t)?;
    let t0 = std::time::Instant::now();
    let ft = FullText::build(&mut g, &mut Reader::new(dir))?;
    eprintln!("full text built in {:.1?}", t0.elapsed());
    let mut d6 = D6::new(dir);
    let mut f = std::fs::File::create(out)?;
    for line in std::fs::read_to_string(qpath)?.lines().filter(|l| !l.trim().is_empty()) {
        let q: serde_json::Value = serde_json::from_str(line)?;
        let question = q["question"].as_str().unwrap_or_default().to_string();
        let gold: HashSet<String> = match &q["gold"] {
            serde_json::Value::Array(v) => v.iter().filter_map(|x| x.as_str().map(String::from)).collect(),
            serde_json::Value::Object(m) => m.keys().cloned().collect(),
            _ => HashSet::new(),
        };
        let hits = ft.search(&question);
        let order: Vec<String> = hits.iter().map(|h| h.0.clone()).collect();
        let seeds: Vec<String> = order.iter().take(3).cloned().collect();
        let seen: HashSet<&String> = seeds.iter().collect();
        let mut doors: BTreeMap<String, serde_json::Value> = BTreeMap::new();
        for s in &seeds {
            for mut c in doors_of(&mut g, s, 100)? {
                c.targets.retain(|d| !seen.contains(d));
                if c.targets.is_empty() || doors.contains_key(&c.key) {
                    continue;
                }
                let text = d6.lines(&c, &mut g)?.join("\n");
                let behind = c.targets.iter().filter(|d| gold.contains(*d)).count();
                doors.insert(c.key.clone(), serde_json::json!({"kind": c.kind, "width": c.targets.len(), "gold": behind, "text": text}));
            }
        }
        let mut walks = serde_json::Map::new();
        let arms: Vec<(&str, Box<dyn Decider>)> = vec![
            ("oracle", Box::new(Oracle(gold.clone()))),
            ("width", Box::new(Width)),
            ("coin", Box::new(Random(Coin::new(&format!("e2e:{}", q["qid"]))))),
            ("search-order", Box::new(SearchOrder::new(&order))),
        ];
        for (name, mut dec) in arms {
            let w = if seeds.is_empty() { None } else { Some(run(&mut g, order.clone(), settings(), &question, dec.as_mut(), &mut d6)?) };
            let mut reads: Vec<(u32, usize, String)> = w.map(|w| w.reads.into_iter().map(|r| (r.wave, r.ord, r.doc)).collect()).unwrap_or_default();
            reads.sort();
            let docs: Vec<String> = reads.into_iter().map(|r| r.2).take(20).collect();
            walks.insert(name.into(), serde_json::json!(docs));
        }
        let row = serde_json::json!({"qid": q["qid"], "search": order.iter().take(20).collect::<Vec<_>>(), "seeds": seeds,
                                     "doors": doors, "walks": walks, "gold": gold.iter().collect::<Vec<_>>()});
        writeln!(f, "{row}")?;
    }
    eprintln!("done in {:.1?}", t0.elapsed());
    Ok(())
}
