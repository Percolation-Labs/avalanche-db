//! The README is the acceptance test. Every `console` block runs in order against a fresh
//! copy of the example, and each command's output must match the block, with only
//! durations masked. `no-test` blocks are skipped; `needs-key` blocks run only when
//! AVALANCHE_MODEL_KEY is set; commands in `fails` blocks must exit non-zero. Every other block runs with no key, so the recorded model
//! answers are what it sees.

use std::path::{Path, PathBuf};
use std::process::Command;

struct Cmd {
    line: String,
    expected: Vec<String>,
    needs_key: bool,
    fails: bool,
}

fn blocks(readme: &str) -> Vec<Cmd> {
    let mut out = vec![];
    let mut in_block: Option<Vec<String>> = None;
    for line in readme.lines() {
        if let Some(flags) = line.strip_prefix("```console") {
            if flags.contains("no-test") {
                in_block = Some(vec!["skip".into()]);
            } else {
                in_block = Some(flags.split_whitespace().map(String::from).collect());
            }
            continue;
        }
        let Some(flags) = &in_block else { continue };
        if line.starts_with("```") {
            in_block = None;
            continue;
        }
        if flags.iter().any(|f| f == "skip") {
            continue;
        }
        if let Some(c) = line.strip_prefix("$ ") {
            out.push(Cmd { line: c.to_string(), expected: vec![], needs_key: flags.iter().any(|f| f == "needs-key"), fails: flags.iter().any(|f| f == "fails") });
        } else if let Some(last) = out.last_mut() {
            last.expected.push(line.to_string());
        }
    }
    for c in &mut out {
        while c.expected.last().is_some_and(|l| l.trim().is_empty()) {
            c.expected.pop();
        }
    }
    out
}

/// Durations vary by machine: `101µs`, `3.2ms` and `1.5s` all become `#µs`. Wall-clock
/// times (`2026-10-24 11:39Z`) become `#time`; dates alone are data and stay.
fn mask(s: &str) -> String {
    let words: Vec<String> = s.split(' ').map(String::from).collect();
    let mut joined = vec![];
    let mut i = 0;
    while i < words.len() {
        let is_date = |w: &str| w.len() == 10 && w.as_bytes()[4] == b'-' && w.as_bytes()[7] == b'-';
        let is_time = |w: &str| w.len() == 6 && w.ends_with('Z') && w.as_bytes()[2] == b':';
        if i + 1 < words.len() && is_date(&words[i]) && is_time(&words[i + 1]) {
            joined.push("#time".to_string());
            i += 2;
        } else {
            joined.push(words[i].clone());
            i += 1;
        }
    }
    let s = joined.join(" ");
    let mut out = String::new();
    let b: Vec<char> = s.trim_end().chars().collect();
    let mut i = 0;
    while i < b.len() {
        if b[i].is_ascii_digit() && (i == 0 || !b[i - 1].is_alphanumeric()) {
            let mut j = i;
            while j < b.len() && (b[j].is_ascii_digit() || b[j] == '.') {
                j += 1;
            }
            let at = |k: usize| b.get(j + k).copied();
            let skip = match (at(0), at(1)) {
                (Some('µ' | 'm'), Some('s')) => 2,
                (Some('s'), next) if !next.is_some_and(char::is_alphanumeric) => 1,
                _ => 0,
            };
            if skip > 0 {
                out += "#µs";
                i = j + skip;
                continue;
            }
        }
        out.push(b[i]);
        i += 1;
    }
    out
}

fn copy(from: &Path, to: &Path) {
    std::fs::create_dir_all(to).unwrap();
    for e in std::fs::read_dir(from).unwrap() {
        let e = e.unwrap();
        let name = e.file_name().to_string_lossy().into_owned();
        // A run left in the example folder must not leak into the test.
        if ["repo", "avalanche.toml", "store.redb"].contains(&name.as_str()) {
            continue;
        }
        if e.path().is_dir() {
            copy(&e.path(), &to.join(&name));
        } else {
            std::fs::copy(e.path(), to.join(&name)).unwrap();
        }
    }
}

#[test]
fn the_readme_story_runs_as_written() {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let readme = std::fs::read_to_string(root.join("README.md")).unwrap();
    let work = std::env::temp_dir().join(format!("ava-readme-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&work);
    copy(&root.join("examples"), &work.join("examples"));
    let bin = PathBuf::from(env!("CARGO_BIN_EXE_ava"));
    let path = format!("{}:{}", bin.parent().unwrap().display(), std::env::var("PATH").unwrap_or_default());
    let has_key = std::env::var("AVALANCHE_MODEL_KEY").is_ok_and(|k| !k.is_empty());
    let mut cwd = work.clone();
    let mut ran = 0;
    for c in blocks(&readme) {
        if let Some(d) = c.line.strip_prefix("cd ") {
            cwd = cwd.join(d.trim());
            continue;
        }
        if c.needs_key && !has_key {
            continue;
        }
        let mut cmd = Command::new("sh");
        cmd.arg("-c").arg(&c.line).current_dir(&cwd).env("PATH", &path).env("HOME", &work);
        if !c.needs_key {
            cmd.env_remove("AVALANCHE_MODEL_KEY");
        }
        let out = cmd.output().unwrap();
        let got = String::from_utf8_lossy(&out.stdout);
        assert_eq!(out.status.success(), !c.fails, "`{}` exited {}:\n{}{}", c.line, out.status, got, String::from_utf8_lossy(&out.stderr));
        let got: Vec<String> = got.lines().map(mask).collect();
        let want: Vec<String> = c.expected.iter().map(|l| mask(l)).collect();
        assert_eq!(got, want, "\n`{}` printed something other than the README says.\n--- README\n{}\n--- ava\n{}\n", c.line, want.join("\n"), got.join("\n"));
        ran += 1;
    }
    assert!(ran >= 10, "only {ran} commands ran; the README lost its story");
    let _ = std::fs::remove_dir_all(&work);
}

#[test]
fn masking_hides_only_durations() {
    assert_eq!(mask("12 keys in 101µs at T2"), "12 keys in #µs at T2");
    assert_eq!(mask("read 5.5s, written 3.2ms"), "read #µs, written #µs");
    assert_eq!(mask("7 commits, 2 steps"), "7 commits, 2 steps");
    assert_eq!(mask("T1  2026-10-24 11:39Z  54 facts"), "T1  #time  54 facts");
    assert_eq!(mask("issue:BUG-12  2026-04-09 \"A cent\""), "issue:BUG-12  2026-04-09 \"A cent\"");
}
