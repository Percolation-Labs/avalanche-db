//! WALK: the seven questions reach.py's walk may ask of a store (p8-subsystems REM-1191,
//! `Store`), answered from the indexes of an imported world. Every list of items comes back
//! in creation order (node id order), so two engines read a clue's targets in one order.

use std::collections::HashMap;

use crate::model::Pred;
use crate::store::{Dir, ScanCost, Store};
use crate::Result;

pub struct World<'a> {
    store: &'a Store,
    t: u32,
    as_of: u64,
    /// Vectors are read once per walk; a walk is pinned to one snapshot.
    vecs: HashMap<u64, Vec<f32>>,
    pub cost: std::cell::Cell<u64>,
}

impl<'a> World<'a> {
    pub fn open(store: &'a Store, t: u32) -> Result<World<'a>> {
        Ok(World { store, t, as_of: store.head(t)?, vecs: store.vectors(t)?.into_iter().collect(), cost: Default::default() })
    }

    fn edges(&self, node: u64, dir: Dir, pred: Pred) -> Result<Vec<u64>> {
        let mut c = ScanCost::default();
        let out = self.store.edges(self.t, node, dir, self.as_of, None, &mut c)?.into_iter().filter(|e| e.pred == pred).map(|e| e.other).collect();
        self.cost.set(self.cost.get() + c.keys_read);
        Ok(out)
    }

    pub fn id(&self, name: &str) -> Result<Option<u64>> {
        self.store.id(self.t, name)
    }

    /// `item:d12` is `d12`, `lit:t3.5` is `t3.5`: the names reach.py uses.
    pub fn name(&self, id: u64) -> Result<String> {
        let n = self.store.name(self.t, id)?;
        Ok(n.split_once(':').map(|(_, r)| r.to_string()).unwrap_or(n))
    }

    /// The `k` items nearest `v` by dot product, best first, ties to the earlier item.
    pub fn nearest(&self, v: &[f32], k: usize) -> Vec<u64> {
        let mut s: Vec<(f64, u64)> = self.vecs.iter().map(|(id, x)| (crate::construct::world::dot(x, v), *id)).collect();
        s.sort_by(|a, b| b.0.total_cmp(&a.0).then(a.1.cmp(&b.1)));
        s.into_iter().take(k).map(|(_, id)| id).collect()
    }

    pub fn vector(&self, i: u64) -> Option<&[f32]> {
        self.vecs.get(&i).map(Vec::as_slice)
    }

    pub fn tags_of(&self, i: u64) -> Result<Vec<u64>> {
        self.edges(i, Dir::Out, Pred::Tagged)
    }

    pub fn tag_members(&self, tag: u64) -> Result<Vec<u64>> {
        self.edges(tag, Dir::In, Pred::Tagged)
    }

    /// Up to two items either side in the item's sitting.
    pub fn next(&self, i: u64) -> Result<Vec<u64>> {
        let Some(s) = self.edges(i, Dir::Out, Pred::InSitting)?.first().copied() else { return Ok(vec![]) };
        let xs = self.edges(s, Dir::In, Pred::InSitting)?;
        let k = xs.iter().position(|x| *x == i).unwrap();
        Ok((k.saturating_sub(2)..(k + 3).min(xs.len())).filter(|j| *j != k).map(|j| xs[j]).collect())
    }

    /// The nearest in meaning, both ways.
    pub fn near(&self, i: u64) -> Result<Vec<u64>> {
        let mut v = self.edges(i, Dir::Out, Pred::Near)?;
        v.extend(self.edges(i, Dir::In, Pred::Near)?);
        v.sort();
        v.dedup();
        Ok(v)
    }

    /// makes and answers, both ways.
    pub fn linked(&self, i: u64) -> Result<Vec<u64>> {
        let mut v = vec![];
        for p in [Pred::Makes, Pred::Answers] {
            v.extend(self.edges(i, Dir::Out, p)?);
            v.extend(self.edges(i, Dir::In, p)?);
        }
        v.sort();
        v.dedup();
        Ok(v)
    }
}
