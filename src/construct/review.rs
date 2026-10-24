//! CONSTRUCT, by a person: a review takes a link back. The link is retracted in the store,
//! so it is gone from now on and still there as of any earlier T, and the rejection is
//! written as facts of its own (`review:N`, its reason, what it retracts). Reviews are also
//! kept in `.avalanche/reviews.jsonl`, beside the model's recorded decisions, so a rebuilt
//! store reads them back at ingest and dreaming never writes a rejected link again.

use std::collections::HashSet;
use std::io::Write;
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::config::DIR;
use crate::model::{lit, FactIn, Pred};
use crate::store::{Dir, ScanCost, Store};
use crate::Result;

pub const FILE: &str = "reviews.jsonl";

#[derive(Serialize, Deserialize)]
pub struct Review {
    pub review: String,
    pub s: String,
    pub p: String,
    pub o: String,
    pub because: String,
    pub at: i64,
}

impl Review {
    pub fn link(&self) -> String {
        format!("{} {} {}", self.s, self.p, self.o)
    }

    fn facts(&self) -> Vec<FactIn> {
        vec![
            FactIn::new(&self.review, Pred::Label, lit(&self.because), "review").at(self.at),
            FactIn::new(&self.review, Pred::Retracts, lit(&self.link()), "review").at(self.at),
        ]
    }
}

pub fn read(dir: &Path) -> Result<Vec<Review>> {
    let Ok(text) = std::fs::read_to_string(dir.join(DIR).join(FILE)) else { return Ok(vec![]) };
    text.lines().filter(|l| !l.trim().is_empty()).map(|l| Ok(serde_json::from_str(l)?)).collect()
}

/// The reviews as facts, for ingest: what a rebuilt store must know was rejected.
pub fn facts(dir: &Path) -> Result<(usize, Vec<FactIn>)> {
    let reviews = read(dir)?;
    Ok((reviews.len(), reviews.iter().flat_map(Review::facts).collect()))
}

/// Every link a review has taken back, as `s p o`.
pub fn rejected(store: &Store, t: u32) -> Result<HashSet<String>> {
    let head = store.head(t)?;
    store
        .by_pred(t, Pred::Retracts, head, &mut ScanCost::default())?
        .into_iter()
        .map(|(_, o, _)| Ok(store.name(t, o)?.trim_start_matches("lit:").to_string()))
        .collect()
}

/// Take back one live link, with the reason, as one transaction.
pub fn retract(store: &Store, t: u32, dir: &Path, s: &str, p: Pred, o: &str, because: &str) -> Result<(u64, Review)> {
    let head = store.head(t)?;
    let sid = store.id(t, s)?.ok_or_else(|| format!("{s} is not in the store"))?;
    let oid = store.id(t, o)?.ok_or_else(|| format!("{o} is not in the store"))?;
    let edge = store
        .edges(t, sid, Dir::Out, head, None, &mut ScanCost::default())?
        .into_iter()
        .find(|e| e.pred == p && e.other == oid)
        .ok_or_else(|| format!("no live link {s} {} {o}", p.name()))?;
    let graph = store.name(t, edge.graph)?.trim_start_matches("graph:").to_string();
    let review = Review { review: format!("review:{}", read(dir)?.len() + 1), s: s.into(), p: p.name().into(), o: o.into(), because: because.into(), at: crate::store::now() };
    let mut gone = FactIn::new(s, p, o, &graph);
    gone.valid_from = Some(edge.valid_from);
    gone.retract = true;
    let mut facts = vec![gone];
    facts.extend(review.facts());
    let tx = store.write(t, &facts)?;
    let mut f = std::fs::OpenOptions::new().create(true).append(true).open(dir.join(DIR).join(FILE))?;
    writeln!(f, "{}", serde_json::to_string(&review)?)?;
    Ok((tx, review))
}
