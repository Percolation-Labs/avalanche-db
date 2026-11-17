//! CONSTRUCT, for a folder: `midb init` and `midb ingest` as functions, so the CLI and the MCP `ingest` tool run
//! the same code and print the same report.

use std::path::{Path, PathBuf};

use super::{ingest, review};
use crate::config::{Config, SourceCfg, DIR, FILE};
use crate::store::Store;
use crate::Result;

/// Write avalanche.toml from what is in the folder, and create the store.
pub fn init(dir: &Path) -> Result<String> {
    if dir.join(FILE).exists() {
        return Err(format!("{FILE} already exists; edit it, or remove it to start again").into());
    }
    let cfg = Config::discover(dir)?;
    std::fs::write(dir.join(FILE), cfg.to_toml())?;
    std::fs::create_dir_all(dir.join(DIR))?;
    let store = Store::open(Config::store_path(dir))?;
    store.tenant(&cfg.tenant)?;
    let mut out = format!("created {FILE} and {DIR}/store.redb (tenant \"{}\")\n", cfg.tenant);
    let srcs: Vec<String> = cfg.sources.iter().map(|s| format!("{} {}", s.adapter, s.path.display())).collect();
    out += &format!("  sources: {}\n", if srcs.is_empty() { "none found".into() } else { srcs.join(", ") });
    let ids: Vec<String> = cfg.ids.iter().map(|(k, v)| format!("{k} {v}")).collect();
    out += &format!("  ids: {}\n", if ids.is_empty() { "none found".into() } else { ids.join(", ") });
    Ok(out)
}

/// Read the configured sources (all, or those named) into the store as one transaction, or a facts file instead.
pub fn ingest(dir: &Path, sources: &[String], facts: Option<PathBuf>) -> Result<String> {
    let started = std::time::Instant::now();
    let cfg = Config::load(dir)?;
    ingest_from(dir, &cfg, sources, facts, started)
}

/// `midb ingest --documents PATH` and the MCP `ingest_repo`: make `path` a `documents` source (creating the config
/// and store when there are none), then ingest that source alone.
pub fn ingest_documents(dir: &Path, path: &str) -> Result<String> {
    let mut out = String::new();
    if Config::add_documents(dir, path)? {
        out += &format!("added a documents source for {path} to {FILE}\n");
    }
    Ok(out + &ingest(dir, &[path.to_string()], None)?)
}

fn ingest_from(dir: &Path, cfg: &Config, sources: &[String], facts: Option<PathBuf>, started: std::time::Instant) -> Result<String> {
    let store = Store::open(Config::store_path(dir))?;
    let t = store.tenant(&cfg.tenant)?;
    let mut out = String::new();
    let mut all = vec![];
    if let Some(f) = facts {
        all = ingest::json_lines(&f)?;
        out += &format!("facts     {}  →  {} facts\n", f.display(), all.len());
    } else {
        let at_of = |src: &SourceCfg| if src.adapter == "github" { src.repo.clone().unwrap_or_default() } else { src.path.display().to_string() };
        if let Some(missing) = sources.iter().find(|n| !cfg.sources.iter().any(|s| at_of(s) == **n)) {
            return Err(format!("{missing}: not a source in {FILE}").into());
        }
        for src in cfg.sources.iter().filter(|s| sources.is_empty() || sources.contains(&at_of(s))) {
            let at = at_of(src);
            let got = match src.adapter.as_str() {
                "git" => ingest::git_history(&dir.join(&src.path), src.rev.as_deref().unwrap_or("HEAD"), &at, cfg)?,
                "markdown" => match &src.rev {
                    Some(rev) => ingest::markdown_at(&dir.join(&src.path), rev, src.dir.as_deref().unwrap_or("."), &at, cfg)?,
                    None => ingest::markdown(&dir.join(&src.path), &at, cfg)?,
                },
                "percolate" => ingest::percolate(&dir.join(&src.path), &at, cfg)?,
                "documents" => super::documents::documents(&dir.join(&src.path), &at, &store, t)?,
                "github" => ingest::github(src.repo.as_deref().ok_or("a github source needs repo = \"owner/name\"")?, cfg)?,
                other => return Err(format!("{other}: no such adapter").into()),
            };
            out += &format!("{:<9} {:<14} {} {:<8} →  {} facts\n", src.adapter, at, got.read.0, got.read.1, got.facts.len());
            all.extend(got.facts);
        }
        let (n, facts) = review::facts(dir)?;
        if n > 0 {
            out += &format!("{:<9} {:<14} {} {:<8} →  {} facts\n", "reviews", format!("{DIR}/{}", review::FILE).trim_start_matches(".avalanche/"), n, if n == 1 { "review" } else { "reviews" }, facts.len());
            all.extend(facts);
        }
    }
    let tx = store.write(t, &all)?;
    out += &format!("T{tx}: {} facts in {:.1?}\n", all.len(), started.elapsed());
    Ok(out)
}
