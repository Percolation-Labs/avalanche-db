//! The `documents` adapter end to end: a folder of your own becomes passages, the walk's graph and D6 doors, with no
//! model and no lab import; and the doors never carry the question (D6's signature has none, and nothing here gives
//! it one).

use std::path::{Path, PathBuf};
use std::process::Command;

fn midb(dir: &Path, args: &[&str]) -> String {
    let out = Command::new(env!("CARGO_BIN_EXE_midb")).arg("--dir").arg(dir).args(args).output().unwrap();
    assert!(out.status.success(), "midb {args:?}: {}", String::from_utf8_lossy(&out.stderr));
    String::from_utf8_lossy(&out.stdout).into_owned()
}

fn folder() -> PathBuf {
    let dir = std::env::temp_dir().join(format!("midb-documents-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&dir);
    std::fs::create_dir_all(dir.join("notes")).unwrap();
    let w = |p: &str, t: &str| std::fs::write(dir.join(p), t).unwrap();
    w("notes/rounding.md", "# Rounding\n\nInvoices round every total half-even, as ADR-007 decided after BUG-12.\n\n## Why half-even\n\nRounding halves away from zero drifts a cent on long invoices, which RoundingPolicy avoids.\n");
    w("notes/export.md", "# Export\n\nThe spreadsheet export writes each invoice total with its currency symbol, through SheetWriter.\n");
    w("notes/support.md", "# Support\n\nA customer said their invoice total was a cent off from their own spreadsheet; RoundingPolicy explained it.\n");
    w("avalanche.toml", "tenant = \"me\"\n\n[[source]]\nadapter = \"documents\"\npath = \"notes\"\n");
    std::fs::create_dir_all(dir.join(".avalanche")).unwrap();
    dir
}

#[test]
fn a_folder_becomes_passages_doors_and_a_full_text_search() {
    let dir = folder();
    let said = midb(&dir, &["ingest"]);
    assert!(said.starts_with("documents notes"), "{said}");
    assert!(said.contains("4 passages"), "{said}");

    let found = midb(&dir, &["search", "--text", "why is the invoice a cent off"]);
    let first = found.lines().next().unwrap();
    assert!(first.contains("support.md#1") || first.contains("rounding.md#2"), "{found}");

    let doors = midb(&dir, &["doors", "support.md#1"]);
    // a term the support note shares with the rounding note opens onto it, and D6 names what is behind it
    assert!(doors.contains("term:roundingpolicy\n  term 'roundingpolicy' · 1 unread"), "{doors}");
    assert!(doors.contains("Names in its 1 unread passage(s): RoundingPolicy"), "{doors}");
    // the near door has two targets: the first as today's snippet, the other as a lead, its title then its opening
    // sentence, without its heading again
    let near = doors.split("near:support.md#1\n").nth(1).expect("a near door");
    assert!(near.starts_with("  2 unread closest in wording to a read one\n"), "{near}");
    assert!(near.contains(": Rounding halves away from zero") || near.contains(": The spreadsheet export writes"), "{near}");
    assert!(!near.contains(": # ") && !near.contains(": ## "), "{near}");
    // no door carries words that are only in a question
    assert!(!doors.contains("why is"), "{doors}");
    std::fs::remove_dir_all(&dir).unwrap();
}

#[test]
fn a_deep_path_is_stored_and_read_back() {
    // a stored value is cut at 120 characters; a passage's path lives in its id, so any depth ingests
    let dir = std::env::temp_dir().join(format!("midb-deep-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&dir);
    let deep = "notes/".to_string() + &"a-rather-long-folder-name/".repeat(6);
    std::fs::create_dir_all(dir.join(&deep)).unwrap();
    std::fs::write(dir.join(&deep).join("deep.md"), "# Deep\n\nA passage far down the tree, about RoundingPolicy.\n").unwrap();
    std::fs::write(dir.join("notes/near.md"), "# Near\n\nAnother passage about RoundingPolicy, near the top.\n").unwrap();
    std::fs::write(dir.join("avalanche.toml"), "tenant = \"me\"\n\n[[source]]\nadapter = \"documents\"\npath = \"notes\"\n").unwrap();
    std::fs::create_dir_all(dir.join(".avalanche")).unwrap();
    assert!(midb(&dir, &["ingest"]).contains("2 passages"));
    let doors = midb(&dir, &["doors", "near.md#1"]);
    assert!(doors.contains("A passage far down the tree"), "{doors}");
    std::fs::remove_dir_all(&dir).unwrap();
}
