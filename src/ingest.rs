//! Adapters. Each reads a source, emits typed facts, and points back to where the
//! content lives; no document text is stored, only short labels. Ingestion is mechanical:
//! an id a source names becomes a plain `mentions` link, and `ava dream` decides later what
//! the mention means.

use std::path::{Path, PathBuf};
use std::process::Command;

use crate::config::Config;
use crate::model::{date, lit, FactIn, Pred};
use crate::Result;

fn git(repo: &Path, args: &[&str]) -> Result<String> {
    let out = Command::new("git").arg("-C").arg(repo).args(args).output()?;
    if !out.status.success() {
        return Err(format!("git {}: {}", args.join(" "), String::from_utf8_lossy(&out.stderr)).into());
    }
    Ok(String::from_utf8_lossy(&out.stdout).into_owned())
}

pub struct Ingested {
    pub facts: Vec<FactIn>,
    /// What was read, for the report: (count, noun).
    pub read: (usize, &'static str),
}

/// A repository's history: commits, parents, author, files touched, and every id a commit
/// message names. Valid time is the author time. `at` is the source path as configured,
/// which pointers carry so `dream` can read the message back.
pub fn git_history(repo: &Path, at: &str, cfg: &Config) -> Result<Ingested> {
    let out = git(repo, &["log", "HEAD", "--name-only", "--format=%x1e%H%x1f%P%x1f%an%x1f%at%x1f%s"])?;
    let mut facts = vec![];
    let mut commits = 0;
    for rec in out.split('\x1e').filter(|r| !r.trim().is_empty()) {
        let mut lines = rec.lines();
        let head: Vec<&str> = lines.next().unwrap_or("").split('\x1f').collect();
        if head.len() < 5 {
            continue;
        }
        commits += 1;
        let (sha, parents, author, t, subject) = (head[0], head[1], head[2], head[3].parse::<i64>().unwrap_or(0), head[4]);
        let c = format!("commit:{}", &sha[..10]);
        facts.push(FactIn::new(&c, Pred::Label, lit(subject), "repo").at(t));
        facts.push(FactIn::new(&c, Pred::Pointer, lit(&format!("git:{at}@{sha}")), "repo").at(t));
        facts.push(FactIn::new(&c, Pred::AuthoredBy, format!("person:{author}"), "repo").at(t));
        for p in parents.split_whitespace() {
            facts.push(FactIn::new(&c, Pred::Parent, format!("commit:{}", &p[..10]), "repo").at(t));
        }
        for node in cfg.ids_in(subject) {
            facts.push(FactIn::new(&c, Pred::Mentions, node, "repo").at(t));
        }
        for file in lines.filter(|l| !l.trim().is_empty()).take(40) {
            facts.push(FactIn::new(&c, Pred::Touches, format!("file:{file}"), "repo").at(t));
        }
    }
    Ok(Ingested { facts, read: (commits, "commits") })
}

/// One markdown note: frontmatter (`id`, `kind`, `title`, `date`) and its body.
pub struct Note {
    pub path: PathBuf,
    pub id: Option<String>,
    pub kind: Option<String>,
    pub title: Option<String>,
    pub date: Option<i64>,
    pub body: String,
}

pub fn read_note(path: &Path) -> Result<Note> {
    let text = std::fs::read_to_string(path)?;
    let (front, body) = match text.strip_prefix("---\n").and_then(|r| r.split_once("\n---\n")) {
        Some((f, b)) => (f, b.to_string()),
        None => ("", text.clone()),
    };
    let field = |k: &str| front.lines().find_map(|l| l.strip_prefix(&format!("{k}:")).map(|v| v.trim().to_string()));
    Ok(Note { path: path.to_path_buf(), id: field("id"), kind: field("kind"), title: field("title"), date: field("date").and_then(|d| date::parse(&d)), body })
}

/// The notes directly in a folder, by file name.
pub fn notes_in(dir: &Path) -> Result<Vec<Note>> {
    let mut paths: Vec<PathBuf> = std::fs::read_dir(dir)?.filter_map(|e| e.ok().map(|e| e.path())).filter(|p| p.extension().is_some_and(|x| x == "md")).collect();
    paths.sort();
    paths.iter().map(|p| read_note(p)).collect()
}

/// Paths a note names in backticks, such as `src/invoice/round.rs`.
fn paths_in(text: &str) -> Vec<String> {
    let mut out = vec![];
    for (i, part) in text.split('`').enumerate() {
        if i % 2 == 1 && part.contains('/') && part.contains('.') && !part.contains(' ') && !out.contains(&part.to_string()) {
            out.push(part.to_string());
        }
    }
    out
}

/// Notes with an id whose prefix the table knows: label, date, where the note lives, and
/// a mention of every other id and every path it names.
pub fn markdown(dir: &Path, at: &str, cfg: &Config) -> Result<Ingested> {
    let notes = notes_in(dir)?;
    let mut facts = vec![];
    let mut read = 0;
    for n in &notes {
        let Some(node) = n.id.as_deref().and_then(|id| cfg.node_for_id(id)) else { continue };
        read += 1;
        let t = n.date.unwrap_or(0);
        let file = n.path.file_name().unwrap().to_string_lossy();
        facts.push(FactIn::new(&node, Pred::Label, lit(n.title.as_deref().unwrap_or(&node)), "notes").at(t));
        facts.push(FactIn::new(&node, Pred::Pointer, lit(&format!("md:{at}/{file}")), "notes").at(t));
        for other in cfg.ids_in(&n.body).into_iter().filter(|o| *o != node) {
            facts.push(FactIn::new(&node, Pred::Mentions, other, "notes").at(t));
        }
        for path in paths_in(&n.body) {
            facts.push(FactIn::new(&node, Pred::Mentions, format!("file:{path}"), "notes").at(t));
        }
    }
    Ok(Ingested { facts, read: (read, "notes") })
}

/// JSON lines of facts by name, as an agent or another adapter writes them.
pub fn json_lines(path: &Path) -> Result<Vec<FactIn>> {
    let text = std::fs::read_to_string(path)?;
    text.lines()
        .enumerate()
        .filter(|(_, l)| !l.trim().is_empty() && !l.trim_start().starts_with("//"))
        .map(|(i, l)| serde_json::from_str(l).map_err(|e| format!("{}:{}: {e}", path.display(), i + 1).into()))
        .collect()
}

/// The text a node's pointer leads to: a commit's message or a note's body.
pub fn content(dir: &Path, pointer: &str) -> Result<String> {
    if let Some(rest) = pointer.strip_prefix("git:") {
        let (repo, sha) = rest.rsplit_once('@').ok_or("bad git pointer")?;
        return git(&dir.join(repo), &["log", "-1", "--format=%B", sha]);
    }
    if let Some(rest) = pointer.strip_prefix("md:") {
        return Ok(read_note(&dir.join(rest))?.body);
    }
    Err(format!("no reader for pointer {pointer}").into())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ids_follow_the_table() {
        let cfg: Config = toml::from_str("tenant = \"t\"\n[ids]\nADR = \"decision\"\nBUG = \"issue\"\n").unwrap();
        assert_eq!(cfg.ids_in("Fix BUG-12 per ADR-007 (BUG-12 again), XYZ-3, BUG-, ADR-7a"), vec!["issue:BUG-12", "decision:ADR-007"]);
    }

    #[test]
    fn paths_come_from_backticks() {
        assert_eq!(paths_in("edit `src/a/b.rs` not `a word` or `x.y`"), vec!["src/a/b.rs"]);
    }
}
