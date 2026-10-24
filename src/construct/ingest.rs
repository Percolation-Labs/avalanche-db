//! CONSTRUCT, mechanically: adapters. Each reads a source, emits typed facts, and points back to where the
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
pub fn git_history(repo: &Path, rev: &str, at: &str, cfg: &Config) -> Result<Ingested> {
    let out = git(repo, &["log", rev, "--name-only", "--format=%x1e%H%x1f%P%x1f%an%x1f%at%x1f%s"])?;
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
    Ok(parse_note(path, &std::fs::read_to_string(path)?))
}

fn parse_note(path: &Path, text: &str) -> Note {
    let text = text.to_string();
    let (front, body) = match text.strip_prefix("---\n").and_then(|r| r.split_once("\n---\n")) {
        Some((f, b)) => (f, b.to_string()),
        None => ("", text.clone()),
    };
    let field = |k: &str| front.lines().find_map(|l| l.strip_prefix(&format!("{k}:")).map(|v| v.trim().to_string()));
    Note { path: path.to_path_buf(), id: field("id"), kind: field("kind"), title: field("title"), date: field("date").or_else(|| field("created")).and_then(|d| date::parse(&d)), body }
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
    let pointers = notes.iter().map(|n| format!("md:{at}/{}", n.path.file_name().unwrap().to_string_lossy())).collect();
    note_facts(&notes, pointers, cfg)
}

/// Notes from a folder inside a git repository at a revision, so a stale working tree
/// does not matter: `git cat-file --batch` reads them all in one process.
pub fn markdown_at(repo: &Path, rev: &str, sub: &str, at: &str, cfg: &Config) -> Result<Ingested> {
    use std::io::{BufRead, Read, Write as _};
    let paths: Vec<String> = git(repo, &["ls-tree", "-r", "--name-only", rev, &format!("{}/", sub.trim_end_matches('/'))])?.lines().filter(|l| l.ends_with(".md")).map(String::from).collect();
    let mut child = Command::new("git").arg("-C").arg(repo).args(["cat-file", "--batch"]).stdin(std::process::Stdio::piped()).stdout(std::process::Stdio::piped()).spawn()?;
    let wanted: String = paths.iter().map(|p| format!("{rev}:{p}\n")).collect();
    let mut stdin = child.stdin.take().unwrap();
    let writer = std::thread::spawn(move || stdin.write_all(wanted.as_bytes()));
    let mut reader = std::io::BufReader::new(child.stdout.take().unwrap());
    let mut notes = vec![];
    for p in &paths {
        let mut header = String::new();
        reader.read_line(&mut header)?;
        let size: usize = header.split_whitespace().nth(2).and_then(|s| s.parse().ok()).unwrap_or(0);
        let mut buf = vec![0u8; size + 1];
        reader.read_exact(&mut buf)?;
        notes.push(parse_note(Path::new(p), &String::from_utf8_lossy(&buf[..size])));
    }
    writer.join().map_err(|_| "git cat-file writer")??;
    child.wait()?;
    let pointers = paths.iter().map(|p| format!("mdgit:{at}@{rev}:{p}")).collect();
    note_facts(&notes, pointers, cfg)
}

fn note_facts(notes: &[Note], pointers: Vec<String>, cfg: &Config) -> Result<Ingested> {
    let mut facts = vec![];
    let mut read = 0;
    for (n, pointer) in notes.iter().zip(pointers) {
        let Some(node) = n.id.as_deref().and_then(|id| cfg.node_for_id(id)) else { continue };
        read += 1;
        let t = n.date.unwrap_or(0);
        facts.push(FactIn::new(&node, Pred::Label, lit(n.title.as_deref().unwrap_or(&node)), "notes").at(t));
        facts.push(FactIn::new(&node, Pred::Pointer, lit(&pointer), "notes").at(t));
        for other in cfg.ids_in(&n.body).into_iter().filter(|o| *o != node) {
            facts.push(FactIn::new(&node, Pred::Mentions, other, "notes").at(t));
        }
        for path in paths_in(&n.body) {
            facts.push(FactIn::new(&node, Pred::Mentions, format!("file:{path}"), "notes").at(t));
        }
    }
    Ok(Ingested { facts, read: (read, "notes") })
}

/// Merged pull requests: title, where they live, the commit they merged as, and every id
/// the title, body or branch names. Valid time is the merge time. Needs `gh`.
pub fn github(slug: &str, cfg: &Config) -> Result<Ingested> {
    let out = Command::new("gh")
        .args(["pr", "list", "--repo", slug, "--state", "merged", "--limit", "5000", "--json", "number,title,body,headRefName,mergeCommit,mergedAt"])
        .output()?;
    if !out.status.success() {
        return Err(format!("gh pr list {slug}: {}", String::from_utf8_lossy(&out.stderr)).into());
    }
    let prs: Vec<serde_json::Value> = serde_json::from_slice(&out.stdout)?;
    let name = slug.rsplit('/').next().unwrap_or(slug);
    let mut facts = vec![];
    for pr in &prs {
        let n = pr["number"].as_u64().unwrap_or(0);
        let node = format!("pr:{name}#{n}");
        let t = pr["mergedAt"].as_str().and_then(date::parse).unwrap_or(0);
        let title = pr["title"].as_str().unwrap_or_default();
        facts.push(FactIn::new(&node, Pred::Label, lit(title), "github").at(t));
        facts.push(FactIn::new(&node, Pred::Pointer, lit(&format!("gh:{slug}#{n}")), "github").at(t));
        if let Some(oid) = pr["mergeCommit"]["oid"].as_str() {
            facts.push(FactIn::new(&node, Pred::MergedAs, format!("commit:{}", &oid[..10]), "github").at(t));
        }
        let text = format!("{title}\n{}\n{}", pr["headRefName"].as_str().unwrap_or_default(), pr["body"].as_str().unwrap_or_default());
        for id in cfg.ids_in(&text) {
            facts.push(FactIn::new(&node, Pred::Mentions, id, "github").at(t));
        }
    }
    Ok(Ingested { facts, read: (prs.len(), "PRs") })
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

/// How much of a change a dream reads: enough for a model to see what changed, bounded
/// so one huge commit cannot dominate the bill.
pub const EVIDENCE_CHARS: usize = 6000;

/// The evidence a node's pointer leads to: a commit's message, the files it changed and
/// its diff, bounded; or a note's body.
pub fn evidence(dir: &Path, pointer: &str) -> Result<String> {
    if let Some(rest) = pointer.strip_prefix("git:") {
        let (repo, sha) = rest.rsplit_once('@').ok_or("bad git pointer")?;
        let text = git(&dir.join(repo), &["show", "--stat", "--patch", "--format=%B", sha])?;
        return Ok(text.chars().take(EVIDENCE_CHARS).collect());
    }
    if let Some(rest) = pointer.strip_prefix("md:") {
        return Ok(read_note(&dir.join(rest))?.body);
    }
    if let Some(rest) = pointer.strip_prefix("mdgit:") {
        let (repo, spec) = rest.split_once('@').ok_or("bad mdgit pointer")?;
        return Ok(parse_note(Path::new(spec), &git(&dir.join(repo), &["show", spec])?).body.chars().take(EVIDENCE_CHARS).collect());
    }
    if let Some(rest) = pointer.strip_prefix("gh:") {
        let (slug, n) = rest.split_once('#').ok_or("bad gh pointer")?;
        let out = Command::new("gh").args(["pr", "view", n, "--repo", slug, "--json", "title,body,files", "--jq", ".title + \"\\n\\n\" + .body + \"\\n\\nfiles: \" + ([.files[].path] | join(\", \"))"]).output()?;
        return Ok(String::from_utf8_lossy(&out.stdout).chars().take(EVIDENCE_CHARS).collect());
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
        assert_eq!(cfg.ids_in("branch amartey/bug-3-export-fix"), vec!["issue:BUG-3"]);
    }

    #[test]
    fn paths_come_from_backticks() {
        assert_eq!(paths_in("edit `src/a/b.rs` not `a word` or `x.y`"), vec!["src/a/b.rs"]);
    }
}
