//! D6: today's best door (p8-subsystems `meta/lab/worlds/mq_doors.py`, `door` under MQ_DOOR=D6; the reference-world
//! result, `results/reference-world/RESULT.md`). Every line is built from ingestion-time data and the door's unread
//! targets, never from the question:
//!
//!   head     what the door is and how many unread passages are behind it
//!   first    today's first snippet: the first target in a fixed hash order, 160 characters
//!   leads    up to five other targets, those naming the most first (hash order the tie): `- title: first sentence`
//!   names    the names its unread targets mention, the most shared first, then the rarest, at most fifteen
//!
//! Two differences from the lab's D6, both forced by the binary: the tie order is sha-256 of `key:doc`, not md5,
//! and names come from `documents::names` (capitalised runs and code identifiers), not spaCy's entities.

use std::collections::{BTreeMap, HashMap};
use std::path::Path;

use sha2::{Digest, Sha256};

use super::doors::{Attrs, DoorLabeller};
use super::lab::{Clue, Graph};
use crate::construct::documents::{lead, Reader};
use crate::model::Pred;
use crate::Result;

pub struct D6 {
    reader: Reader,
    /// doc → (title, text, names)
    docs: HashMap<String, (String, String, Vec<String>)>,
    /// name → how many documents name it, filled as documents are read
    df: BTreeMap<String, usize>,
}

fn hash(key: &str, doc: &str) -> Vec<u8> {
    Sha256::digest(format!("{key}:{doc}").as_bytes()).to_vec()
}

fn snippet(text: &str, n: usize) -> String {
    text.split_whitespace().collect::<Vec<_>>().join(" ").chars().take(n).collect()
}

/// A passage's text without what its title already says: leading markdown headings, and a first line the title
/// carries (a commit's subject).
fn body(title: &str, text: &str) -> String {
    let mut lines = text.lines().skip_while(|l| l.trim().is_empty() || l.trim_start().starts_with('#')).peekable();
    // the stored title is cut at 120 characters, so a long subject is matched on its opening
    let opens = |l: &str| title.contains(&l.trim().chars().take(40).collect::<String>());
    if lines.peek().is_some_and(|l| !l.trim().is_empty() && opens(l)) {
        lines.next();
    }
    let rest = lines.collect::<Vec<_>>().join("\n");
    if rest.trim().is_empty() { text.to_string() } else { rest.trim().to_string() }
}

impl D6 {
    /// `dir` is the folder holding avalanche.toml, against which pointers resolve.
    pub fn new(dir: &Path) -> D6 {
        D6 { reader: Reader::new(dir), docs: HashMap::new(), df: BTreeMap::new() }
    }

    fn doc(&mut self, d: &str, g: &mut Graph) -> Result<&(String, String, Vec<String>)> {
        if !self.docs.contains_key(d) {
            let title = g.values(d, Pred::Label)?.into_iter().next().unwrap_or_else(|| d.to_string());
            let text = match g.values(d, Pred::Pointer)?.into_iter().next() {
                Some(p) => self.reader.text(d, &p)?,
                None => String::new(),
            };
            let names = g.values(d, Pred::Named)?;
            for n in &names {
                *self.df.entry(n.clone()).or_default() += 1;
            }
            self.docs.insert(d.to_string(), (title, text, names));
        }
        Ok(&self.docs[d])
    }

    /// The door's text, one line per entry; `immediate.join("\n")` is what a decider is shown.
    pub fn lines(&mut self, door: &Clue, g: &mut Graph) -> Result<Vec<String>> {
        let tg = &door.targets;
        let head = match door.kind.as_str() {
            "term" => format!("term '{}' · {} unread", door.x, tg.len()),
            "near" => format!("{} unread closest in wording to a read one", tg.len()),
            "next" => format!("{} unread beside a read one, in the same file or history", tg.len()),
            k => format!("{k} · {} unread", tg.len()),
        };
        for d in tg {
            self.doc(d, g)?;
        }
        let mut by_hash: Vec<&String> = tg.iter().collect();
        by_hash.sort_by_key(|d| hash(&door.key, d));
        let mut lines = vec![head];
        let mut shown = String::new();
        if let Some(first) = by_hash.first() {
            let (title, text, _) = &self.docs[*first];
            shown = snippet(&format!("{title}\n\n{text}"), 160);
            lines.push(format!("- {shown}"));
        }
        let mut ordered: Vec<&String> = tg.iter().collect();
        ordered.sort_by_key(|d| (std::cmp::Reverse(self.docs[*d].2.len()), hash("", d)));
        let mut leads = 0;
        for d in ordered {
            if leads == 5 {
                break;
            }
            let (title, text, _) = &self.docs[d];
            let opening: String = snippet(text, 40);
            if !opening.is_empty() && shown.contains(&opening) {
                continue;
            }
            lines.push(format!("- {}: {}", snippet(title, 120), lead(&body(title, text), 200)));
            leads += 1;
        }
        let mut count: BTreeMap<&str, usize> = BTreeMap::new();
        for d in tg {
            let mut seen: Vec<&str> = self.docs[d].2.iter().map(String::as_str).collect();
            seen.sort();
            seen.dedup();
            for n in seen {
                *count.entry(n).or_default() += 1;
            }
        }
        let mut named: Vec<(&str, usize)> = count.into_iter().collect();
        named.sort_by(|a, b| b.1.cmp(&a.1).then(self.df.get(a.0).cmp(&self.df.get(b.0))).then(a.0.cmp(b.0)));
        if !named.is_empty() {
            let list: Vec<&str> = named.iter().take(15).map(|(n, _)| *n).collect();
            lines.push(format!("Names in its {} unread passage(s): {}.", tg.len(), list.join(", ")));
        }
        Ok(lines)
    }
}

impl DoorLabeller for D6 {
    fn version(&self) -> String {
        "d6/1".into()
    }
    fn label(&mut self, door: &Clue, g: &mut Graph) -> Result<Attrs> {
        let mut stats = BTreeMap::new();
        stats.insert("targets".into(), door.targets.len() as f64);
        if door.kind == "term" {
            stats.insert("postings".into(), g.post(&door.x)?.len() as f64);
        }
        Ok(Attrs { kind: door.kind.clone(), immediate: self.lines(door, g)?, reachable: None, stats })
    }
}

/// The doors reading `doc` would raise, every other passage unread: a term door per term it holds (held by at most
/// `cap` passages), and its `next` and `near` doors. As the walk raises them (`lab::raise`), for one read.
pub fn doors_of(g: &mut Graph, doc: &str, cap: usize) -> Result<Vec<Clue>> {
    if !g.holds(doc) {
        return Err(format!("{doc}: no such passage (ids are as `midb search --text` prints them)").into());
    }
    let mut out = vec![];
    for t in g.terms(doc)? {
        let post = g.post(&t)?;
        if post.len() > cap {
            continue;
        }
        let tg: Vec<String> = post.into_iter().filter(|d| d != doc).collect();
        if !tg.is_empty() {
            out.push(Clue { key: format!("term:{t}"), kind: "term".into(), x: t, source: doc.into(), targets: tg, wave: 0, p: None });
        }
    }
    for (kind, pred) in [("next", Pred::Beside), ("near", Pred::Near)] {
        let mut tg: Vec<String> = g.list(pred, doc)?.into_iter().filter(|d| d != doc).collect();
        tg.sort();
        if !tg.is_empty() {
            out.push(Clue { key: format!("{kind}:{doc}"), kind: kind.into(), x: doc.into(), source: doc.into(), targets: tg, wave: 0, p: None });
        }
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    #[test]
    fn body_drops_what_the_title_says() {
        assert_eq!(super::body("a.md › Part", "## Part\n\nThe part says this."), "The part says this.");
        assert_eq!(super::body("commit 1a2b3c4: fix rounding", "fix rounding\n\nBanker's rounding, per ADR-007."), "Banker's rounding, per ADR-007.");
        assert_eq!(super::body("x", "## Only a heading"), "## Only a heading");
    }
}
