//! CONSTRUCT: the walk lab's graphs (p8-subsystems `bill/walklab`, `meta/lab`, REM-1172 stage A) read into a store, one
//! tenant per conversation, so Avalanche can walk the lab's fixture from its own indexes and be held to the lab's
//! engine read for read.
//!
//! A line of `graphs.jsonl` is `{conv, graph: {keys, terms, post, beside, near}}`. The graph's documents (`keys`'
//! values) are labelled first, in that order, so a node id is a document's place in the graph. A term is a value
//! (`tagged`), so the documents holding it are the term's incoming edges: `post` is not stored, because it is the
//! inverse of `terms` (checked here). `beside` and `near` are the lab's lists, one way, as given.

use std::collections::{BTreeMap, BTreeSet};
use std::path::Path;

use crate::model::{lit, FactIn, Pred};
use crate::store::Store;
use crate::Result;

const GRAPH: &str = "lab";

/// A conversation's tenant.
pub fn tenant_name(conv: &str) -> String {
    format!("lab-{conv}")
}

pub fn item(doc: &str) -> String {
    format!("item:{doc}")
}

pub fn term(t: &str) -> Result<String> {
    let name = format!("lit:{t}");
    if lit(t) != name {
        return Err(format!("term {t:?} would be stored as {:?}; the lab's term would be lost", lit(t)).into());
    }
    Ok(name)
}

pub struct Imported {
    pub conv: String,
    pub docs: usize,
    pub facts: usize,
}

pub fn import(store: &Store, graphs: &Path, only: Option<&str>) -> Result<Vec<Imported>> {
    let mut out = vec![];
    for line in std::fs::read_to_string(graphs)?.lines().filter(|l| !l.is_empty()) {
        let v: serde_json::Value = serde_json::from_str(line)?;
        let conv = v["conv"].as_str().ok_or("a graph line has no conv")?.to_string();
        if only.is_some_and(|o| o != conv) {
            continue;
        }
        let g = &v["graph"];
        let keys: Vec<String> = g["keys"].as_object().ok_or("no keys")?.values().map(|d| d.as_str().unwrap_or_default().to_string()).collect();
        let list = |k: &str| -> Result<BTreeMap<String, Vec<String>>> {
            let o = g[k].as_object().ok_or_else(|| format!("{conv}: no {k}"))?;
            Ok(o.iter().map(|(d, xs)| (d.clone(), xs.as_array().map(|a| a.iter().filter_map(|x| x.as_str().map(String::from)).collect()).unwrap_or_default())).collect())
        };
        let (terms, post, beside, near) = (list("terms")?, list("post")?, list("beside")?, list("near")?);
        let mut inv: BTreeMap<&str, BTreeSet<&str>> = BTreeMap::new();
        for (d, ts) in &terms {
            for t in ts {
                inv.entry(t).or_default().insert(d);
            }
        }
        let post_set: BTreeMap<&str, BTreeSet<&str>> = post.iter().map(|(t, ds)| (t.as_str(), ds.iter().map(String::as_str).collect())).collect();
        if inv != post_set {
            return Err(format!("{conv}: post is not the inverse of terms, so it cannot be read from the term index").into());
        }

        let mut facts: Vec<FactIn> = keys.iter().map(|d| FactIn::new(item(d), Pred::Label, format!("lit:{d}"), GRAPH)).collect();
        for d in &keys {
            for t in terms.get(d).into_iter().flatten() {
                facts.push(FactIn::new(item(d), Pred::Tagged, term(t)?, GRAPH));
            }
            for (pred, m) in [(Pred::Beside, &beside), (Pred::Near, &near)] {
                for x in m.get(d).into_iter().flatten() {
                    facts.push(FactIn::new(item(d), pred, item(x), GRAPH));
                }
            }
        }
        let t = store.tenant(&tenant_name(&conv))?;
        if store.head(t)? > 0 {
            return Err(format!("{conv} is already imported; import into a fresh store").into());
        }
        store.write(t, &facts)?;
        out.push(Imported { conv, docs: keys.len(), facts: facts.len() });
    }
    Ok(out)
}
