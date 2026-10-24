//! Adapters. Each reads a source, emits typed facts, and points back to where the
//! content lives; no document text is stored, only short labels.

use std::io::{BufRead, Write};
use std::path::Path;
use std::process::{Command, Stdio};

use crate::model::{date, lit, FactIn, Pred};
use crate::Result;

fn git(repo: &Path, args: &[&str]) -> Result<String> {
    let out = Command::new("git").arg("-C").arg(repo).args(args).output()?;
    if !out.status.success() {
        return Err(format!("git {}: {}", args.join(" "), String::from_utf8_lossy(&out.stderr)).into());
    }
    Ok(String::from_utf8_lossy(&out.stdout).into_owned())
}

fn cards_in(text: &str) -> Vec<String> {
    let mut out = vec![];
    let b = text.as_bytes();
    let mut i = 0;
    while let Some(pos) = text[i..].find("REM-") {
        let start = i + pos + 4;
        let end = start + b[start..].iter().take_while(|c| c.is_ascii_digit()).count();
        if end > start {
            let id = format!("card:REM-{}", &text[start..end]);
            if !out.contains(&id) {
                out.push(id);
            }
        }
        i = end.max(start);
    }
    out
}

/// A repository's history: commits, parents, authors, files touched, and the cards a
/// commit message names. Valid time is the author time.
pub fn git_history(repo: &Path, rev: &str, max: Option<usize>) -> Result<Vec<FactIn>> {
    let name = repo.canonicalize()?.file_name().map(|s| s.to_string_lossy().into_owned()).unwrap_or_default();
    let mut args = vec!["log", rev, "--name-only", "--format=%x1e%H%x1f%P%x1f%an%x1f%at%x1f%s"];
    let max_arg;
    if let Some(m) = max {
        max_arg = format!("--max-count={m}");
        args.push(&max_arg);
    }
    let out = git(repo, &args)?;
    let mut facts = vec![];
    for rec in out.split('\x1e').filter(|r| !r.trim().is_empty()) {
        let mut lines = rec.lines();
        let head: Vec<&str> = lines.next().unwrap_or("").split('\x1f').collect();
        if head.len() < 5 {
            continue;
        }
        let (sha, parents, author, at, subject) = (head[0], head[1], head[2], head[3].parse::<i64>().unwrap_or(0), head[4]);
        let c = format!("commit:{}", &sha[..10]);
        facts.push(FactIn::new(&c, Pred::Label, lit(subject), "repo").at(at));
        facts.push(FactIn::new(&c, Pred::Pointer, lit(&format!("git:{name}@{sha}")), "repo").at(at));
        facts.push(FactIn::new(&c, Pred::AuthoredBy, format!("person:{author}"), "repo").at(at));
        for p in parents.split_whitespace() {
            facts.push(FactIn::new(&c, Pred::Parent, format!("commit:{}", &p[..10]), "repo").at(at));
        }
        for card in cards_in(subject) {
            facts.push(FactIn::new(&c, Pred::Mentions, card, "repo").at(at));
        }
        for file in lines.filter(|l| !l.trim().is_empty()).take(40) {
            facts.push(FactIn::new(&c, Pred::Touches, format!("file:{file}"), "repo").at(at));
        }
    }
    Ok(facts)
}

/// Board cards at a revision: title, state, and where the card lives. The card is the
/// decision; commits reach it through `mentions`.
pub fn board_cards(repo: &Path, rev: &str) -> Result<Vec<FactIn>> {
    let paths: Vec<String> = git(repo, &["ls-tree", "-r", "--name-only", rev, "board/cards/"])?.lines().filter(|l| l.ends_with(".md")).map(String::from).collect();
    let mut child = Command::new("git").arg("-C").arg(repo).args(["cat-file", "--batch"]).stdin(Stdio::piped()).stdout(Stdio::piped()).spawn()?;
    {
        let mut stdin = child.stdin.take().unwrap();
        let wanted: String = paths.iter().map(|p| format!("{rev}:{p}\n")).collect();
        std::thread::spawn(move || stdin.write_all(wanted.as_bytes()));
    }
    let mut reader = std::io::BufReader::new(child.stdout.take().unwrap());
    let mut facts = vec![];
    for path in &paths {
        let mut header = String::new();
        reader.read_line(&mut header)?;
        let size: usize = header.split_whitespace().nth(2).and_then(|s| s.parse().ok()).unwrap_or(0);
        let mut buf = vec![0u8; size + 1];
        std::io::Read::read_exact(&mut reader, &mut buf)?;
        let text = String::from_utf8_lossy(&buf);
        let field = |k: &str| text.lines().take(20).find_map(|l| l.strip_prefix(&format!("{k}: ")).map(|v| v.trim().to_string()));
        let Some(id) = field("id") else { continue };
        let at = field("created").and_then(|d| date::parse(&d)).unwrap_or(0);
        let card = format!("card:{id}");
        facts.push(FactIn::new(&card, Pred::Label, lit(&field("title").unwrap_or_default()), "board").at(at));
        facts.push(FactIn::new(&card, Pred::State, lit(&field("state").unwrap_or_default()), "board").at(at));
        facts.push(FactIn::new(&card, Pred::Pointer, lit(&format!("board:{rev}:{path}")), "board").at(at));
    }
    child.wait()?;
    Ok(facts)
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

#[cfg(test)]
mod tests {
    #[test]
    fn finds_card_ids() {
        assert_eq!(super::cards_in("Fix REM-12 and REM-1172 (REM-12 again), REM- none"), vec!["card:REM-12", "card:REM-1172"]);
    }
}
