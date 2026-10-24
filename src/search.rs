//! The circle: lexical likeness (BM25) between a question and node labels. `ava search`
//! shows it so a reader can see what search alone returns, and `ava ask` uses it once to
//! pick where a walk starts.

use std::collections::{BTreeMap, HashMap};

use crate::model::{Kind, Pred};
use crate::store::{ScanCost, Store};
use crate::Result;

const STOP: &[&str] = &["a", "an", "and", "are", "as", "at", "be", "by", "do", "does", "for", "from", "how", "in", "is", "it", "of", "on", "or", "s", "the", "this", "to", "was", "what", "when", "where", "which", "who", "why", "with"];

pub fn terms(text: &str) -> Vec<String> {
    text.to_lowercase()
        .split(|c: char| !c.is_alphanumeric())
        .filter(|w| !w.is_empty() && !STOP.contains(w))
        .map(|w| if w.len() > 3 && w.ends_with('s') && !w.ends_with("ss") { w[..w.len() - 1].to_string() } else { w.to_string() })
        .collect()
}

pub struct Hit {
    pub node: String,
    pub label: String,
    pub score: f64,
}

/// Every labelled node valid at `valid_at` (all of them when None), scored against the
/// words; only nodes sharing at least one word are returned, best first.
pub fn search(store: &Store, t: u32, words: &str, as_of: u64, valid_at: Option<i64>) -> Result<Vec<Hit>> {
    let q = terms(words);
    let mut docs = vec![];
    for (s, o, _) in store.by_pred(t, Pred::Label, as_of, &mut ScanCost::default())? {
        let node = store.name(t, s)?;
        if matches!(Kind::of(&node), Some(Kind::Session | Kind::Step) | None) {
            continue;
        }
        if let Some(at) = valid_at {
            let e = store.edges(t, s, crate::store::Dir::Out, as_of, Some(at), &mut ScanCost::default())?;
            if !e.iter().any(|e| e.pred == Pred::Label) {
                continue;
            }
        }
        let label = store.name(t, o)?.trim_start_matches("lit:").to_string();
        docs.push((node, terms(&label), label));
    }
    let n = docs.len() as f64;
    let avg = docs.iter().map(|d| d.1.len()).sum::<usize>() as f64 / n.max(1.0);
    let mut df: HashMap<&str, f64> = HashMap::new();
    for d in &docs {
        let mut seen: Vec<&str> = d.1.iter().map(String::as_str).collect();
        seen.sort();
        seen.dedup();
        for w in seen {
            *df.entry(w).or_default() += 1.0;
        }
    }
    let (k1, b) = (1.2, 0.75);
    let mut hits = vec![];
    for (node, toks, label) in &docs {
        let mut tf: BTreeMap<&str, f64> = BTreeMap::new();
        for w in toks {
            *tf.entry(w).or_default() += 1.0;
        }
        let mut score = 0.0;
        for w in &q {
            let Some(f) = tf.get(w.as_str()) else { continue };
            let idf = ((n - df[w.as_str()] + 0.5) / (df[w.as_str()] + 0.5) + 1.0).ln();
            score += idf * f * (k1 + 1.0) / (f + k1 * (1.0 - b + b * toks.len() as f64 / avg));
        }
        if score > 0.0 {
            hits.push(Hit { node: node.clone(), label: label.clone(), score });
        }
    }
    hits.sort_by(|a, b| b.score.total_cmp(&a.score).then(a.node.cmp(&b.node)));
    Ok(hits)
}
