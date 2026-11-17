//! DESCRIBE: a door as the lab and the product show it to Jev (p8-subsystems `meta/lab/walklab/describe.py`,
//! `lines`; percolate's aiq.walk_describe_clue), ported character for character so a request built here is the
//! request the lab sends (`tests/jev.rs` holds the bytes to the Python's).
//!
//! Up to three of the door's unread targets, chosen by md5(key || ':' || doc); each is the document's own text
//! (whitespace collapsed, 160 characters) and where it sits relative to the door's source. The labeller has no
//! question argument: a door's text never depends on the question (Sirsh, M-20261115-201816-ab76).

use std::collections::{BTreeMap, HashMap};
use std::path::Path;

use md5::{Digest, Md5};
use serde::Deserialize;

use super::doors::{Attrs, DoorLabeller};
use super::lab::{Clue, Graph};
use crate::Result;

/// One document as the lab's docs.jsonl holds it.
#[derive(Clone, Debug, Default, Deserialize)]
pub struct Doc {
    pub uri: String,
    #[serde(default)]
    pub title: Option<String>,
    #[serde(default)]
    pub said: Option<String>,
    #[serde(default)]
    pub sitting: Option<serde_json::Value>,
    #[serde(default)]
    pub position: Option<i64>,
    #[serde(default)]
    pub said_at: Option<String>,
}

pub type Docs = HashMap<String, Doc>;

/// A docs.jsonl, keyed by uri.
pub fn load(path: &Path) -> Result<Docs> {
    let mut out = HashMap::new();
    for line in std::fs::read_to_string(path).map_err(|e| format!("{}: {e}", path.display()))?.lines().filter(|l| !l.trim().is_empty()) {
        let d: Doc = serde_json::from_str(line)?;
        out.insert(d.uri.clone(), d);
    }
    Ok(out)
}

/// Python's `str.isspace`: Rust's whitespace and the four separators \x1c to \x1f.
fn py_space(c: char) -> bool {
    c.is_whitespace() || ('\x1c'..='\x1f').contains(&c)
}

/// `re.sub(r"\s+", " ", text).strip()[:n]`, n in characters.
pub fn collapse(text: &str, n: usize) -> String {
    text.split(py_space).filter(|w| !w.is_empty()).collect::<Vec<_>>().join(" ").chars().take(n).collect()
}

fn md5_hex(s: &str) -> String {
    Md5::digest(s.as_bytes()).iter().map(|b| format!("{b:02x}")).collect()
}

/// The day of an ISO timestamp, as days since 0000-03-01 (only differences are used).
fn day(ts: &str) -> Option<i64> {
    let (y, m, d) = (ts.get(0..4)?.parse::<i64>().ok()?, ts.get(5..7)?.parse::<i64>().ok()?, ts.get(8..10)?.parse::<i64>().ok()?);
    let (y, m) = if m <= 2 { (y - 1, m + 12) } else { (y, m) };
    Some(365 * y + y / 4 - y / 100 + y / 400 + (153 * (m - 3) + 2) / 5 + d)
}

/// describe.where: the target's place relative to the source.
fn place(t: Option<&Doc>, s: Option<&Doc>) -> String {
    let (Some(t), Some(s)) = (t, s) else { return String::new() };
    let sit = |d: &Doc| d.sitting.clone().filter(|v| !v.is_null());
    if sit(t).is_some() && sit(t) == sit(s) {
        if let (Some(tp), Some(sp)) = (t.position, s.position) {
            return format!(" (same sitting, {} exchange(s) {})", (tp - sp).abs(), if tp < sp { "earlier" } else { "later" });
        }
    }
    let at = |d: &Doc| d.said_at.clone().filter(|x| !x.is_empty());
    if let (Some(ta), Some(sa)) = (at(t), at(s)) {
        if let (Some(dt), Some(ds)) = (day(&ta), day(&sa)) {
            if dt == ds {
                return " (another sitting, the same day)".into();
            }
            return format!(" (another sitting, {} day(s) {})", (dt - ds).abs(), if ta < sa { "earlier" } else { "later" });
        }
    }
    String::new()
}

fn side(kind: &str) -> &'static str {
    match kind {
        "next" => "just before and after a read one, in the same sitting",
        "near" => "closest in meaning to a read one",
        "title" => "about something a read one names",
        _ => "joined to a read one by a sentence",
    }
}

/// describe.lines for one door: `unread` its unread targets, `postings` the documents holding its term.
pub fn lines(c: &Clue, unread: &[String], docs: &Docs, postings: usize) -> String {
    let mut at: Vec<(String, &String)> = unread.iter().map(|d| (md5_hex(&format!("{}:{d}", c.key)), d)).collect();
    at.sort();
    let src = docs.get(&c.source);
    let parts: Vec<String> = at.iter().take(3).map(|(_, d)| {
        let x = docs.get(*d);
        let line = collapse(x.map(|x| x.said.as_deref().unwrap_or("")).unwrap_or(d.as_str()), 160);
        format!("\"{line}\"{}", place(x, src))
    }).collect();
    let body = if parts.is_empty() { "(none)".to_string() } else { parts.join(" | ") };
    if c.kind == "term" {
        return format!("the term '{}', held by {postings} message(s) in all, {} of them unread. What the user said in them: {body}", c.x, unread.len());
    }
    format!("{} unread message(s) {}. What the user said in them: {body}", unread.len(), side(&c.kind))
}

/// The lab's door text as a labeller: `immediate` holds the one line Jev is shown (a decider joins `immediate`
/// with newlines for its option text, as bill's D6 labeller is read).
pub struct Describe<'d> {
    pub docs: &'d Docs,
}

impl DoorLabeller for Describe<'_> {
    fn version(&self) -> String {
        "describe-lines/1".into()
    }
    fn label(&mut self, door: &Clue, g: &mut Graph) -> Result<Attrs> {
        // a door's targets are unread when it is judged: raised from the last wave's reads, judged before the next
        let postings = if door.kind == "term" { g.post(&door.x)?.len() } else { 0 };
        let mut stats = BTreeMap::new();
        stats.insert("targets".into(), door.targets.len() as f64);
        if door.kind == "term" {
            stats.insert("postings".into(), postings as f64);
        }
        Ok(Attrs { kind: door.kind.clone(), immediate: vec![lines(door, &door.targets, self.docs, postings)], reachable: None, stats })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn collapse_is_pythons_whitespace() {
        assert_eq!(collapse("  a\n\nb\x1cc\u{a0}d\t", 160), "a b c d");
        assert_eq!(collapse("é".repeat(200).as_str(), 160).chars().count(), 160);
    }

    #[test]
    fn days_differ_as_dates_do() {
        assert_eq!(day("2026-03-01T10:00:00").unwrap() - day("2026-02-28T23:00:00").unwrap(), 1);
        assert_eq!(day("2024-03-01").unwrap() - day("2024-02-28").unwrap(), 2);
        assert_eq!(day("2027-01-01").unwrap() - day("2026-01-01").unwrap(), 365);
    }
}
