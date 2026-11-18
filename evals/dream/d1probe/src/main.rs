//! D1's store tools (REGISTERED-D1.md). Two modes:
//!
//!     d1-probe dump  STORE_DIR OUT.jsonl        one line per passage: {d, keys (under the cap), next, near}
//!     d1-probe write STORE_DIR HUBS.jsonl       writes each hub {label, members} as one `tagged` literal per member
//!
//! `write` refuses a label the store already holds, so a hub never merges into an existing key.

use std::io::Write;
use std::path::Path;

use avalanche::config::Config;
use avalanche::model::{FactIn, Pred};
use avalanche::store::Store;
use avalanche::walk::lab::Graph;

const CAP: usize = 100;

fn main() -> avalanche::Result<()> {
    let a: Vec<String> = std::env::args().collect();
    let (mode, dir, path) = (a[1].as_str(), Path::new(&a[2]), &a[3]);
    let cfg = Config::load(dir)?;
    let store = Store::open(Config::store_path(dir))?;
    let t = store.tenant(&cfg.tenant)?;
    let mut g = Graph::open_items(&store, t)?;
    match mode {
        "dump" => {
            let mut f = std::io::BufWriter::new(std::fs::File::create(path)?);
            let mut df: std::collections::HashMap<String, usize> = Default::default();
            for d in g.docs() {
                let mut keys = vec![];
                for k in g.terms(&d)? {
                    let n = match df.get(&k) {
                        Some(n) => *n,
                        None => {
                            let n = g.post(&k)?.len();
                            df.insert(k.clone(), n);
                            n
                        }
                    };
                    if n <= CAP && n >= 2 {
                        keys.push(k);
                    }
                }
                let next = g.list(Pred::Beside, &d)?;
                let near = g.list(Pred::Near, &d)?;
                writeln!(f, "{}", serde_json::json!({"d": d, "keys": keys, "next": next, "near": near}))?;
            }
        }
        "write" => {
            let mut facts = vec![];
            for line in std::fs::read_to_string(path)?.lines().filter(|l| !l.trim().is_empty()) {
                let h: serde_json::Value = serde_json::from_str(line)?;
                let label = h["label"].as_str().ok_or("hub without label")?;
                if !g.post(label)?.is_empty() {
                    return Err(format!("{label}: the store already holds this key").into());
                }
                for m in h["members"].as_array().ok_or("hub without members")? {
                    let m = m.as_str().ok_or("member is not a string")?;
                    if !g.holds(m) {
                        return Err(format!("{m}: no such passage").into());
                    }
                    facts.push(FactIn::new(format!("item:{m}"), Pred::Tagged, format!("lit:{label}"), "dream"));
                }
            }
            drop(g);
            let tx = store.write(t, &facts)?;
            println!("T{tx}: {} facts", facts.len());
        }
        _ => return Err("mode is dump or write".into()),
    }
    Ok(())
}
