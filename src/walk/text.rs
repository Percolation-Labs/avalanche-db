//! WALK: search over the passages' full text (BM25), the baseline a walk over ingested documents is measured
//! against and the order it seeds from. `midb search` scores labels only; a passage's label is its title, so this
//! reads each passage's text back through its pointer instead.

use std::collections::HashMap;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use super::lab::Graph;
use crate::construct::documents::{words, Reader};
use crate::model::Pred;
use crate::Result;

/// Every passage's words, read once; then any number of questions.
#[derive(Serialize, Deserialize)]
pub struct FullText {
    docs: Vec<(String, HashMap<String, f64>, f64)>,
    df: HashMap<String, f64>,
    avg: f64,
}

/// Where a store's full-text index is kept, beside the store.
pub fn index_path(dir: &Path) -> PathBuf {
    dir.join(crate::config::DIR).join("fulltext.json")
}

#[derive(Serialize, Deserialize)]
struct Saved {
    tenant: u32,
    head: u64,
    index: FullText,
}

impl FullText {
    /// The index for the tenant at `head`: read from `.avalanche/fulltext.json` when it was built at that head, else
    /// built (reading every passage back) and saved. Ingestion builds it, so a walk in a fresh process reads it
    /// instead of rebuilding: on p8-subsystems the build takes about 10 s.
    pub fn open(dir: &Path, t: u32, head: u64, g: &mut Graph) -> Result<FullText> {
        let path = index_path(dir);
        if let Ok(bytes) = std::fs::read(&path) {
            if let Ok(s) = serde_json::from_slice::<Saved>(&bytes) {
                if s.tenant == t && s.head == head {
                    return Ok(s.index);
                }
            }
        }
        let index = FullText::build(g, &mut Reader::new(dir))?;
        let saved = Saved { tenant: t, head, index };
        let tmp = path.with_extension("json.tmp");
        std::fs::write(&tmp, serde_json::to_vec(&saved)?)?;
        std::fs::rename(&tmp, &path)?;
        Ok(saved.index)
    }

    pub fn build(g: &mut Graph, reader: &mut Reader) -> Result<FullText> {
        let mut docs = vec![];
        let mut df: HashMap<String, f64> = HashMap::new();
        for d in g.docs() {
            let title = g.values(&d, Pred::Label)?.into_iter().next().unwrap_or_default();
            let text = match g.values(&d, Pred::Pointer)?.into_iter().next() {
                Some(p) => reader.text(&d, &p)?,
                None => String::new(),
            };
            let ws = words(&format!("{title}\n{text}"));
            let len = ws.len() as f64;
            let mut tf: HashMap<String, f64> = HashMap::new();
            for w in ws {
                *tf.entry(w).or_default() += 1.0;
            }
            for w in tf.keys() {
                *df.entry(w.clone()).or_default() += 1.0;
            }
            docs.push((d, tf, len));
        }
        let avg = docs.iter().map(|d| d.2).sum::<f64>() / (docs.len() as f64).max(1.0);
        Ok(FullText { docs, df, avg })
    }

    /// Passages sharing a word with the question, best first (BM25, k1 1.2, b 0.75; the id breaks ties).
    pub fn search(&self, question: &str) -> Vec<(String, f64)> {
        let q = words(question);
        let n = self.docs.len() as f64;
        let (k1, b) = (1.2, 0.75);
        let mut out = vec![];
        for (d, tf, len) in &self.docs {
            let mut s = 0.0;
            for w in &q {
                let Some(f) = tf.get(w) else { continue };
                let df = self.df[w];
                s += ((n - df + 0.5) / (df + 0.5) + 1.0).ln() * f * (k1 + 1.0) / (f + k1 * (1.0 - b + b * len / self.avg));
            }
            if s > 0.0 {
                out.push((d.clone(), s));
            }
        }
        out.sort_by(|a, b| b.1.total_cmp(&a.1).then(a.0.cmp(&b.0)));
        out
    }
}
