//! WALK, kept: a question suite. A question whose answer you trust is kept with what its
//! walk reached; `run` walks every kept question again and reports what changed, so a
//! rebuilt index, a new adapter or a review is checked against answers given before.
//! The suite lives in `.avalanche/suite.jsonl`, to be committed beside the store's config.

use std::collections::HashSet;
use std::path::Path;

use serde::{Deserialize, Serialize};

use super::session::{self, parse_prefer};
use crate::config::DIR;
use crate::model::date;
use crate::store::Store;
use crate::Result;

pub const FILE: &str = "suite.jsonl";

#[derive(Serialize, Deserialize)]
pub struct Entry {
    pub question: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub valid_at: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub prefer: Vec<String>,
    pub budget: usize,
    /// What the walk reached, as `parent link node` lines.
    pub reached: Vec<String>,
}

pub struct Outcome {
    pub question: String,
    pub gone: Vec<String>,
    pub new: Vec<String>,
}

fn path(dir: &Path) -> std::path::PathBuf {
    dir.join(DIR).join(FILE)
}

pub fn read(dir: &Path) -> Result<Vec<Entry>> {
    let Ok(text) = std::fs::read_to_string(path(dir)) else { return Ok(vec![]) };
    text.lines().filter(|l| !l.trim().is_empty()).map(|l| Ok(serde_json::from_str(l)?)).collect()
}

fn walk(store: &Store, t: u32, e: &Entry) -> Result<Vec<String>> {
    let valid_at = e.valid_at.as_deref().map(|d| date::through(d).ok_or(format!("{d}: not a date"))).transpose()?;
    Ok(session::reached(&session::walk(store, t, &e.question, e.budget, None, valid_at, &parse_prefer(&e.prefer)?)?))
}

/// Keep a question and what it reaches now, replacing an earlier entry for it.
pub fn add(store: &Store, t: u32, dir: &Path, question: &str, budget: usize, valid_at: Option<String>, prefer: Vec<String>) -> Result<Entry> {
    let mut e = Entry { question: question.into(), valid_at, prefer, budget, reached: vec![] };
    e.reached = walk(store, t, &e)?;
    let mut all: Vec<Entry> = read(dir)?.into_iter().filter(|o| o.question != e.question || o.valid_at != e.valid_at || o.prefer != e.prefer).collect();
    all.push(e);
    let text: String = all.iter().map(|e| Ok(serde_json::to_string(e)? + "\n")).collect::<Result<_>>()?;
    std::fs::write(path(dir), text)?;
    Ok(all.pop().unwrap())
}

/// Walk every kept question again.
pub fn run(store: &Store, t: u32, dir: &Path) -> Result<Vec<Outcome>> {
    read(dir)?
        .into_iter()
        .map(|e| {
            let now = walk(store, t, &e)?;
            let (was, is): (HashSet<&String>, HashSet<&String>) = (e.reached.iter().collect(), now.iter().collect());
            let gone = e.reached.iter().filter(|r| !is.contains(r)).cloned().collect();
            let new = now.iter().filter(|r| !was.contains(r)).cloned().collect();
            Ok(Outcome { question: e.question, gone, new })
        })
        .collect()
}
