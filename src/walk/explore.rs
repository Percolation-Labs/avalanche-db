//! WALK: the exploring walk of p8-subsystems REM-1191 stage 1 (converge.py `explore`), on an
//! imported world. It reads search's first ten, then travels one clue at a time:
//! - with chance 1 - eps, the accepted clue (P >= 0.5) with the fewest unread targets, then
//!   the higher P, then the clue's name;
//! - with chance eps, or when no accepted clue is open, a clue drawn from every open clue in
//!   proportion to its P (only the near misses, P in [band, 0.5), when a band is set and any is open).
//!
//! A clue stays open until its targets are all read; a long tag lands its ten unread members
//! nearest the question per travel. The walk ends when no clue is open.
//!
//! Each clue's P is replayed from a recording (`Decisions`), and the draws come from a
//! portable coin, so this walk and the reference read the same items in the same order.

use std::cmp::Reverse;
use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};

use sha2::{Digest, Sha256};

use super::world::World;
use crate::construct::world::dot;
use crate::Result;

pub const SEEDS: usize = 10;
/// A tag with more members than this is long (REM-1168); one travel lands this many.
pub const LONG: usize = 10;

/// SplitMix64, seeded by the first eight bytes of SHA-256 of a string. reach.py has the same.
pub struct Coin(u64);

impl Coin {
    pub fn new(seed: &str) -> Coin {
        let h = Sha256::digest(seed.as_bytes());
        Coin(u64::from_be_bytes(h[..8].try_into().unwrap()))
    }

    pub fn next(&mut self) -> f64 {
        self.0 = self.0.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^= z >> 31;
        (z >> 11) as f64 * (1.0 / (1u64 << 53) as f64)
    }
}

/// An index drawn in proportion to the weights: the first whose running sum passes u * total.
pub fn choose(w: &[f64], u: f64) -> usize {
    let mut cum = Vec::with_capacity(w.len());
    let mut s = 0.0;
    for x in w {
        s += x;
        cum.push(s);
    }
    let x = u * s;
    cum.iter().position(|c| *c > x).unwrap_or(w.len() - 1).min(w.len() - 1)
}

/// Recorded P per (question, clue kind, clue source), as the reference wrote them.
pub struct Decisions(HashMap<(String, String, String), f64>);

impl Decisions {
    /// JSON lines: `{"qid": "q3", "kind": "tag", "x": "t3.5", "p": 0.81}`.
    pub fn read(text: &str) -> Result<Decisions> {
        let mut m = HashMap::new();
        for line in text.lines().filter(|l| !l.is_empty()) {
            let v: serde_json::Value = serde_json::from_str(line)?;
            let s = |k: &str| v[k].as_str().unwrap_or_default().to_string();
            m.insert((s("qid"), s("kind"), s("x")), v["p"].as_f64().ok_or("no p")?);
        }
        Ok(Decisions(m))
    }

    fn p(&self, qid: &str, kind: &str, x: &str) -> Result<f64> {
        self.0.get(&(qid.to_string(), kind.to_string(), x.to_string())).copied().ok_or_else(|| format!("{qid}: no recorded P for ({kind}, {x})").into())
    }
}

pub struct Opts<'a> {
    pub eps: f64,
    pub max_reads: usize,
    /// Clue kinds given P = 0: a broken condition 2.
    pub blind: &'a [String],
    pub band: Option<f64>,
}

pub struct Walked {
    pub order: Vec<u64>,
    /// The clue kind that read each item: search, short, long, next or near.
    pub why: Vec<&'static str>,
    /// Accepted clues open after each read, and those with at most LONG unread targets.
    pub front: Vec<usize>,
    pub front_small: Vec<usize>,
}

type Clue = (&'static str, u64);

struct State<'w, 'a> {
    w: &'w World<'a>,
    qid: &'w str,
    d: &'w Decisions,
    blind: &'w [String],
    read: HashSet<u64>,
    p: HashMap<Clue, f64>,
    name: HashMap<Clue, String>,
    rem: HashMap<Clue, HashSet<u64>>,
    holders: HashMap<u64, Vec<Clue>>,
    /// Open clues by (kind, name): the order a draw lists them in.
    opened: BTreeMap<(&'static str, String), Clue>,
    /// Open accepted clues, best first.
    best: BTreeSet<(usize, Reverse<u64>, &'static str, String)>,
    front: usize,
}

impl State<'_, '_> {
    fn targets(&self, c: Clue) -> Result<Vec<u64>> {
        match c.0 {
            "tag" => self.w.tag_members(c.1),
            "next" => self.w.next(c.1),
            "near" => self.w.near(c.1),
            _ => self.w.linked(c.1),
        }
    }

    fn key(&self, c: Clue) -> (usize, Reverse<u64>, &'static str, String) {
        (self.rem[&c].len(), Reverse(self.p[&c].to_bits()), c.0, self.name[&c].clone())
    }

    /// Judge and open the clues out of one newly read item; returns how many were accepted.
    fn offer(&mut self, source: u64) -> Result<usize> {
        let mut clues: Vec<Clue> = self.w.tags_of(source)?.into_iter().map(|t| ("tag", t)).collect();
        clues.extend([("next", source), ("near", source)]);
        let mut new = 0;
        for c in clues {
            if self.p.contains_key(&c) {
                continue;
            }
            let name = self.w.name(c.1)?;
            let p = if self.blind.iter().any(|b| b == c.0) { 0.0 } else { self.d.p(self.qid, c.0, &name)? };
            self.p.insert(c, p);
            self.name.insert(c, name.clone());
            new += (p >= 0.5) as usize;
            let rem: HashSet<u64> = self.targets(c)?.into_iter().filter(|x| !self.read.contains(x)).collect();
            if !rem.is_empty() {
                for x in &rem {
                    self.holders.entry(*x).or_default().push(c);
                }
                self.rem.insert(c, rem);
                self.opened.insert((c.0, name), c);
                if p >= 0.5 {
                    self.front += 1;
                    self.best.insert(self.key(c));
                }
            }
        }
        Ok(new)
    }

    /// One item read: every open clue pointing at it has one target fewer.
    fn mark(&mut self, x: u64) {
        for c in self.holders.remove(&x).unwrap_or_default() {
            if !self.opened.contains_key(&(c.0, self.name[&c].clone())) {
                continue;
            }
            let accepted = self.p[&c] >= 0.5;
            if accepted {
                self.best.remove(&self.key(c));
            }
            self.rem.get_mut(&c).unwrap().remove(&x);
            if self.rem[&c].is_empty() {
                self.opened.remove(&(c.0, self.name[&c].clone()));
                self.front -= accepted as usize;
            } else if accepted {
                self.best.insert(self.key(c));
            }
        }
    }
}

pub fn explore(w: &World, qid: &str, qv: &[f32], d: &Decisions, o: &Opts) -> Result<Walked> {
    let mut coin = Coin::new(&format!("walk:{qid}:{}", (o.eps * 1000.0).round() as i64));
    let seeds = w.nearest(qv, SEEDS);
    let mut s = State { w, qid, d, blind: o.blind, read: seeds.iter().copied().collect(), p: HashMap::new(), name: HashMap::new(), rem: HashMap::new(), holders: HashMap::new(), opened: BTreeMap::new(), best: BTreeSet::new(), front: 0 };
    let mut out = Walked { order: seeds.clone(), why: vec!["search"; seeds.len()], front: vec![], front_small: vec![0; seeds.len()] };
    for x in &seeds {
        s.offer(*x)?;
    }
    out.front = vec![s.front; seeds.len()];
    while out.order.len() < o.max_reads && !s.opened.is_empty() {
        let a = s.best.first().map(|(_, _, k, n)| s.opened[&(*k, n.clone())]);
        let c = match a {
            Some(a) if coin.next() >= o.eps => a,
            _ => {
                let mut open: Vec<Clue> = s.opened.values().copied().collect();
                if let Some(band) = o.band {
                    let near: Vec<Clue> = open.iter().copied().filter(|c| band <= s.p[c] && s.p[c] < 0.5).collect();
                    if !near.is_empty() {
                        open = near;
                    }
                }
                let wts: Vec<f64> = open.iter().map(|c| s.p[c]).collect();
                if wts.iter().sum::<f64>() == 0.0 || (o.eps == 0.0 && a.is_none()) {
                    break;
                }
                open[choose(&wts, coin.next())]
            }
        };
        let mut land: Vec<u64> = s.targets(c)?.into_iter().filter(|x| !s.read.contains(x)).collect();
        let long = c.0 == "tag" && w.tag_members(c.1)?.len() > LONG;
        if land.len() > LONG {
            land.sort_by(|a, b| {
                let f = |x: &u64| w.vector(*x).map(|v| -dot(v, qv)).unwrap_or(0.0);
                f(a).total_cmp(&f(b))
            });
            land.truncate(LONG);
        }
        let kind = if c.0 == "tag" { if long { "long" } else { "short" } } else { c.0 };
        for x in &land {
            s.read.insert(*x);
            s.mark(*x);
            out.order.push(*x);
            out.why.push(kind);
        }
        for x in &land {
            s.offer(*x)?;
        }
        let small = s.best.iter().filter(|k| k.0 <= LONG).count();
        out.front.extend(std::iter::repeat_n(s.front, land.len()));
        out.front_small.extend(std::iter::repeat_n(small, land.len()));
    }
    Ok(out)
}
